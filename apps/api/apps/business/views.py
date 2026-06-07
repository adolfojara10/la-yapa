"""Views for /api/v1/business/*."""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.businesses.models import BusinessLocation
from apps.orders.models import Order, OrderStatus
from apps.orders.services import (
    PickupError,
    PinInvalid,
    QrInvalid,
    confirm_pickup_by_pin,
    confirm_pickup_by_qr,
    register_pin_miss,
)
from apps.suspended_meals.models import DonationStatus, SuspendedMealDonation
from apps.suspended_meals.services import (
    DispatchError,
    DispatchRateLimitExceeded,
    DonationNotAvailable,
    NotYourLocation,
    dispatch_donation,
)
from apps.users.auth.permissions import BusinessOwnerOnly, IsEmailVerified

from .serializers import (
    BusinessOrderSerializer,
    ConfirmPickupByIdSerializer,
    ConfirmPickupByPinSerializer,
    ConfirmPickupByScanSerializer,
    DashboardSummarySerializer,
    DispatchSuspendedSerializer,
    SuspendedMealForDispatchSerializer,
)

BUSINESS_PERMISSIONS = [IsAuthenticated, BusinessOwnerOnly, IsEmailVerified]


# Shared helpers --------------------------------------------------------------


def _owned_location_ids(user) -> list[int]:
    return list(BusinessLocation.objects.filter(business__owner=user).values_list("id", flat=True))


_NON_TERMINAL_FOR_BUSINESS = (
    OrderStatus.PAID,
    OrderStatus.READY_FOR_PICKUP,
    OrderStatus.PENDING_REFUND,
)


# Endpoints ------------------------------------------------------------------


class ActiveOrdersView(APIView):
    """GET /api/v1/business/orders/active

    All non-terminal orders across the requester's owned locations,
    sorted by pickup window. Excludes PENDING_PAYMENT (those haven't
    paid yet and shouldn't appear on the vendor's worklist).
    """

    permission_classes = BUSINESS_PERMISSIONS

    def get(self, request):
        owned = _owned_location_ids(request.user)
        if not owned:
            return Response([])
        qs = (
            Order.objects.filter(
                business_location_id__in=owned,
                status__in=_NON_TERMINAL_FOR_BUSINESS,
            )
            .select_related("bag", "consumer__consumer_profile", "business_location")
            .order_by("bag__pickup_window_start")
        )
        return Response(BusinessOrderSerializer(qs, many=True).data)


class TodayOrdersView(APIView):
    """GET /api/v1/business/orders/today — terminal orders from today
    (completed + cancelled + refunded). Used for the dashboard history view."""

    permission_classes = BUSINESS_PERMISSIONS

    def get(self, request):
        owned = _owned_location_ids(request.user)
        if not owned:
            return Response([])
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        qs = (
            Order.objects.filter(
                business_location_id__in=owned,
                status__in=(
                    OrderStatus.COMPLETED,
                    OrderStatus.CANCELLED,
                    OrderStatus.REFUNDED,
                ),
                updated_at__gte=today_start,
            )
            .select_related("bag", "consumer__consumer_profile", "business_location")
            .order_by("-updated_at")
        )
        return Response(BusinessOrderSerializer(qs, many=True).data)


class OrderDetailView(APIView):
    """GET /api/v1/business/orders/{id} — single order detail."""

    permission_classes = BUSINESS_PERMISSIONS

    def get(self, request, pk: str):
        owned = _owned_location_ids(request.user)
        try:
            order = Order.objects.select_related(
                "bag", "consumer__consumer_profile", "business_location"
            ).get(pk=pk, business_location_id__in=owned)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(BusinessOrderSerializer(order).data)


# ----- pickup confirmation --------------------------------------------------


def _pickup_error_to_response(exc: PickupError) -> Response:
    """Map pickup-service exceptions to HTTP responses."""
    status_map = {
        "qr_invalid": status.HTTP_404_NOT_FOUND,
        "pin_invalid": status.HTTP_404_NOT_FOUND,
        "pin_locked": status.HTTP_423_LOCKED,
        "outside_pickup_window": status.HTTP_409_CONFLICT,
        "pickup_invalid_status": status.HTTP_409_CONFLICT,
    }
    return Response(
        {"detail": str(exc), "code": exc.code},
        status=status_map.get(exc.code, status.HTTP_400_BAD_REQUEST),
    )


class ConfirmPickupByScanView(APIView):
    """POST /api/v1/business/orders/confirm-pickup-by-scan
    Body: {qr_token}

    Used by the scanner screen — the QR encodes only the token, not the
    order id. Returns the confirmed (COMPLETED) order on success.
    """

    permission_classes = BUSINESS_PERMISSIONS

    def post(self, request):
        ser = ConfirmPickupByScanSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            order = confirm_pickup_by_qr(
                business_owner=request.user,
                qr_token=str(ser.validated_data["qr_token"]),
            )
        except PickupError as exc:
            return _pickup_error_to_response(exc)
        return Response(BusinessOrderSerializer(order).data, status=status.HTTP_200_OK)


class ConfirmPickupByPinView(APIView):
    """POST /api/v1/business/orders/confirm-pickup-by-pin
    Body: {business_location_id, pin}

    Used by the dashboard's manual entry sheet when the vendor types the
    4-digit code shown on the consumer's order screen.
    """

    permission_classes = BUSINESS_PERMISSIONS

    def post(self, request):
        ser = ConfirmPickupByPinSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        location_id = ser.validated_data["business_location_id"]
        pin = ser.validated_data["pin"]
        try:
            order = confirm_pickup_by_pin(
                business_owner=request.user,
                business_location_id=location_id,
                pin=pin,
            )
        except PinInvalid as exc:
            # Charge the miss to the attempt counter if a matching PAID
            # order actually exists (see register_pin_miss for the "we
            # can't charge a miss on a non-existent PIN" comment).
            register_pin_miss(
                business_owner=request.user,
                business_location_id=location_id,
                pin=pin,
            )
            return _pickup_error_to_response(exc)
        except PickupError as exc:
            return _pickup_error_to_response(exc)
        return Response(BusinessOrderSerializer(order).data, status=status.HTTP_200_OK)


class ConfirmPickupByIdView(APIView):
    """POST /api/v1/business/orders/{id}/confirm-pickup
    Body: {qr_token} OR {pin}

    Spec-required endpoint. The two more-specific variants
    (confirm-pickup-by-scan, confirm-pickup-by-pin) cover the actual
    mobile use cases; this one exists for the documented API contract
    and ad-hoc tooling.
    """

    permission_classes = BUSINESS_PERMISSIONS

    def post(self, request, pk: str):
        ser = ConfirmPickupByIdSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        owned = _owned_location_ids(request.user)
        order = get_object_or_404(Order, pk=pk, business_location_id__in=owned)

        try:
            if ser.validated_data.get("qr_token"):
                if str(ser.validated_data["qr_token"]) != str(order.pickup_qr_token):
                    raise QrInvalid()
                confirmed = confirm_pickup_by_qr(
                    business_owner=request.user,
                    qr_token=str(order.pickup_qr_token),
                )
            else:
                pin = ser.validated_data["pin"]
                try:
                    confirmed = confirm_pickup_by_pin(
                        business_owner=request.user,
                        business_location_id=order.business_location_id,
                        pin=pin,
                    )
                except PinInvalid as exc:
                    register_pin_miss(
                        business_owner=request.user,
                        business_location_id=order.business_location_id,
                        pin=pin,
                    )
                    return _pickup_error_to_response(exc)
        except PickupError as exc:
            return _pickup_error_to_response(exc)

        return Response(BusinessOrderSerializer(confirmed).data, status=status.HTTP_200_OK)


# ----- suspended meals ------------------------------------------------------


class ActiveSuspendedView(APIView):
    """GET /api/v1/business/suspended-meals/active

    Lists ACTIVE donations attributable to the requester's locations:
      - Donations with `bag` set whose bag.business_location is owned
      - General-pool donations (bag=None) — shown to ANY business owner
        as available to dispatch
    """

    permission_classes = BUSINESS_PERMISSIONS

    def get(self, request):
        owned = _owned_location_ids(request.user)
        from django.db.models import Q

        qs = (
            SuspendedMealDonation.objects.filter(
                status=DonationStatus.ACTIVE,
            )
            .filter(Q(bag__business_location_id__in=owned) | Q(bag__isnull=True))
            .select_related("bag__business_location")
            .order_by("-created_at")
        )
        return Response(SuspendedMealForDispatchSerializer(qs, many=True).data)


class DispatchSuspendedView(APIView):
    """POST /api/v1/business/suspended-meals/dispatch
    Body: {donation_id, business_location_id?, notes?}
    """

    permission_classes = BUSINESS_PERMISSIONS

    def post(self, request):
        ser = DispatchSuspendedSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            claim = dispatch_donation(
                business_owner=request.user,
                donation_id=str(ser.validated_data["donation_id"]),
                business_location_id=ser.validated_data.get("business_location_id"),
                notes=ser.validated_data.get("notes", ""),
            )
        except DispatchRateLimitExceeded as exc:
            return Response(
                {"detail": str(exc), "code": exc.code},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except (DonationNotAvailable, NotYourLocation) as exc:
            return Response(
                {"detail": str(exc), "code": exc.code},
                status=status.HTTP_404_NOT_FOUND,
            )
        except DispatchError as exc:
            return Response(
                {"detail": str(exc), "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "claim_id": claim.id,
                "donation_id": str(claim.donation_id),
                "business_location_id": claim.business_location_id,
                "claimed_at": claim.claimed_at,
            },
            status=status.HTTP_200_OK,
        )


class DashboardView(APIView):
    """GET /api/v1/business/dashboard — counts for the home screen header."""

    permission_classes = BUSINESS_PERMISSIONS

    def get(self, request):
        owned = _owned_location_ids(request.user)
        if not owned:
            return Response(
                DashboardSummarySerializer(
                    {
                        "active_orders_count": 0,
                        "today_completed_count": 0,
                        "suspended_meals_available": 0,
                    }
                ).data
            )

        from django.db.models import Q

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        active_orders_count = Order.objects.filter(
            business_location_id__in=owned,
            status__in=_NON_TERMINAL_FOR_BUSINESS,
        ).count()
        today_completed_count = Order.objects.filter(
            business_location_id__in=owned,
            status=OrderStatus.COMPLETED,
            picked_up_at__gte=today_start,
        ).count()
        suspended_count = (
            SuspendedMealDonation.objects.filter(status=DonationStatus.ACTIVE)
            .filter(Q(bag__business_location_id__in=owned) | Q(bag__isnull=True))
            .count()
        )

        return Response(
            DashboardSummarySerializer(
                {
                    "active_orders_count": active_orders_count,
                    "today_completed_count": today_completed_count,
                    "suspended_meals_available": suspended_count,
                }
            ).data
        )
