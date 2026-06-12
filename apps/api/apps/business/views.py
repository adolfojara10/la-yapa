"""Views for /api/v1/business/*."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bags.models import Bag, BagTemplate
from apps.business.services import (
    BusinessServiceError,
    assert_bag_editable,
    duplicate_bag,
    owned_locations_qs,
    primary_business_for_owner,
    submit_onboarding,
)
from apps.businesses.models import BusinessLocation, BusinessStatus
from apps.core.uploads import store_uploaded_file
from apps.geo.utils import make_point
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
    BagDuplicateSerializer,
    BagTemplateSerializer,
    BagTemplateWriteSerializer,
    BagWriteSerializer,
    BusinessAccountSerializer,
    BusinessLocationSerializer,
    BusinessLocationWriteSerializer,
    BusinessOnboardingSerializer,
    BusinessOrderSerializer,
    ConfirmPickupByIdSerializer,
    ConfirmPickupByPinSerializer,
    ConfirmPickupByScanSerializer,
    DashboardSummarySerializer,
    DispatchSuspendedSerializer,
    ManagedBagSerializer,
    SuspendedMealForDispatchSerializer,
)

BUSINESS_PERMISSIONS = [IsAuthenticated, BusinessOwnerOnly, IsEmailVerified]
UPLOAD_PARSERS = [JSONParser, MultiPartParser, FormParser]


def _owned_location_ids(user) -> list[int]:
    return list(owned_locations_qs(user).values_list("id", flat=True))


def _owned_bag_or_404(user, pk: str) -> Bag:
    return get_object_or_404(
        Bag.objects.select_related("business_location__business").prefetch_related(
            "dietary_tags",
            "allergen_warnings",
        ),
        pk=pk,
        business_location__business__owner=user,
    )


def _require_business(user):
    business = primary_business_for_owner(user)
    if business is None:
        raise BusinessServiceError("Complete onboarding first.", code="business_not_onboarded")
    return business


def _require_approved_business(user):
    business = _require_business(user)
    if business.status != BusinessStatus.APPROVED:
        raise BusinessServiceError(
            "Your business must be approved before managing bags.",
            code="business_not_approved",
        )
    return business


def _pickup_error_to_response(exc: PickupError) -> Response:
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


def _business_error_to_response(exc: BusinessServiceError) -> Response:
    status_map = {
        "business_not_onboarded": status.HTTP_409_CONFLICT,
        "business_not_approved": status.HTTP_409_CONFLICT,
        "business_already_approved": status.HTTP_409_CONFLICT,
        "bag_edit_not_allowed": status.HTTP_409_CONFLICT,
    }
    return Response(
        {"detail": str(exc), "code": exc.code},
        status=status_map.get(exc.code, status.HTTP_400_BAD_REQUEST),
    )


_NON_TERMINAL_FOR_BUSINESS = (
    OrderStatus.PAID,
    OrderStatus.READY_FOR_PICKUP,
    OrderStatus.PENDING_REFUND,
)


class OnboardingView(APIView):
    permission_classes = BUSINESS_PERMISSIONS
    parser_classes = UPLOAD_PARSERS

    def post(self, request):
        ser = BusinessOnboardingSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            business = submit_onboarding(
                user=request.user,
                payload=ser.validated_data,
                files=ser.validated_data,
            )
        except BusinessServiceError as exc:
            return _business_error_to_response(exc)
        return Response(BusinessAccountSerializer(business).data, status=status.HTTP_201_CREATED)


class LocationsView(APIView):
    permission_classes = BUSINESS_PERMISSIONS
    parser_classes = UPLOAD_PARSERS

    def get(self, request):
        locations = owned_locations_qs(request.user).order_by("name")
        return Response(BusinessLocationSerializer(locations, many=True).data)

    def post(self, request):
        ser = BusinessLocationWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            business = _require_business(request.user)
        except BusinessServiceError as exc:
            return _business_error_to_response(exc)
        location = BusinessLocation.objects.create(
            business=business,
            name=ser.validated_data["name"],
            address=ser.validated_data["address"],
            location=make_point(ser.validated_data["lat"], ser.validated_data["lng"]),
            phone=ser.validated_data.get("phone", ""),
            is_active=ser.validated_data.get("is_active", True),
            hours_of_operation=ser.validated_data.get("hours_of_operation", {}),
        )
        return Response(BusinessLocationSerializer(location).data, status=status.HTTP_201_CREATED)


class LocationDetailView(APIView):
    permission_classes = BUSINESS_PERMISSIONS
    parser_classes = UPLOAD_PARSERS

    def patch(self, request, pk: int):
        location = get_object_or_404(owned_locations_qs(request.user), pk=pk)
        ser = BusinessLocationWriteSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        if "name" in data:
            location.name = data["name"]
        if "address" in data:
            location.address = data["address"]
        if "lat" in data or "lng" in data:
            lat = data.get("lat", _point(location)["lat"])
            lng = data.get("lng", _point(location)["lng"])
            if lat is None or lng is None:
                return Response(
                    {"detail": "Both lat and lng are required.", "code": "invalid_location"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            location.location = make_point(lat, lng)
        if "phone" in data:
            location.phone = data["phone"]
        if "is_active" in data:
            location.is_active = data["is_active"]
        if "hours_of_operation" in data:
            location.hours_of_operation = data["hours_of_operation"]
        location.save()
        return Response(BusinessLocationSerializer(location).data)


class BagsView(APIView):
    permission_classes = BUSINESS_PERMISSIONS
    parser_classes = UPLOAD_PARSERS

    def get(self, request):
        bags = (
            Bag.objects.filter(business_location__business__owner=request.user)
            .select_related("business_location")
            .prefetch_related("dietary_tags", "allergen_warnings")
            .order_by("-created_at")
        )
        return Response(ManagedBagSerializer(bags, many=True).data)

    def post(self, request):
        ser = BagWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            _require_approved_business(request.user)
        except BusinessServiceError as exc:
            return _business_error_to_response(exc)

        location = get_object_or_404(
            owned_locations_qs(request.user), pk=ser.validated_data["business_location_id"]
        )
        bag = Bag(
            business_location=location,
            type=ser.validated_data["type"],
            title=ser.validated_data["title"],
            description=ser.validated_data.get("description", ""),
            original_price=ser.validated_data["original_price"],
            sale_price=ser.validated_data["sale_price"],
            quantity_available=ser.validated_data["quantity_available"],
            pickup_window_start=ser.validated_data["pickup_window_start"],
            pickup_window_end=ser.validated_data["pickup_window_end"],
            is_active=ser.validated_data.get("is_active", True),
            is_suspended_meal_eligible=ser.validated_data.get(
                "is_suspended_meal_eligible",
                False,
            ),
        )
        if image := ser.validated_data.get("image"):
            bag.image_url = store_uploaded_file(image, prefix="business/bags")
        bag.save()
        bag.dietary_tags.set(ser.validated_data.get("dietary_tags", []))
        bag.allergen_warnings.set(ser.validated_data.get("allergen_warnings", []))
        return Response(ManagedBagSerializer(bag).data, status=status.HTTP_201_CREATED)


class BagDetailView(APIView):
    permission_classes = BUSINESS_PERMISSIONS
    parser_classes = UPLOAD_PARSERS

    def get(self, request, pk: str):
        bag = _owned_bag_or_404(request.user, pk)
        return Response(ManagedBagSerializer(bag).data)

    def patch(self, request, pk: str):
        bag = _owned_bag_or_404(request.user, pk)
        ser = BagWriteSerializer(instance=bag, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        try:
            _require_approved_business(request.user)
            assert_bag_editable(bag)
        except BusinessServiceError as exc:
            return _business_error_to_response(exc)

        data = ser.validated_data
        if "business_location_id" in data:
            bag.business_location = get_object_or_404(
                owned_locations_qs(request.user),
                pk=data["business_location_id"],
            )
        for field in (
            "type",
            "title",
            "description",
            "original_price",
            "sale_price",
            "quantity_available",
            "pickup_window_start",
            "pickup_window_end",
            "is_active",
            "is_suspended_meal_eligible",
        ):
            if field in data:
                setattr(bag, field, data[field])
        if image := data.get("image"):
            bag.image_url = store_uploaded_file(image, prefix="business/bags")
        bag.save()
        if "dietary_tags" in data:
            bag.dietary_tags.set(data["dietary_tags"])
        if "allergen_warnings" in data:
            bag.allergen_warnings.set(data["allergen_warnings"])
        return Response(ManagedBagSerializer(bag).data)


class BagDuplicateView(APIView):
    permission_classes = BUSINESS_PERMISSIONS

    def post(self, request, pk: str):
        bag = _owned_bag_or_404(request.user, pk)
        ser = BagDuplicateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        if "business_location_id" in data:
            get_object_or_404(owned_locations_qs(request.user), pk=data["business_location_id"])
        try:
            _require_approved_business(request.user)
        except BusinessServiceError as exc:
            return _business_error_to_response(exc)
        clone = duplicate_bag(bag=bag, overrides=data)
        return Response(ManagedBagSerializer(clone).data, status=status.HTTP_201_CREATED)


class BagTemplatesView(APIView):
    permission_classes = BUSINESS_PERMISSIONS
    parser_classes = UPLOAD_PARSERS

    def get(self, request):
        try:
            business = _require_business(request.user)
        except BusinessServiceError as exc:
            return _business_error_to_response(exc)
        templates = (
            BagTemplate.objects.filter(business=business)
            .prefetch_related("dietary_tags", "allergen_warnings")
            .order_by("name", "-created_at")
        )
        return Response(BagTemplateSerializer(templates, many=True).data)

    def post(self, request):
        ser = BagTemplateWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            business = _require_approved_business(request.user)
        except BusinessServiceError as exc:
            return _business_error_to_response(exc)
        template = BagTemplate(
            business=business,
            name=ser.validated_data["name"],
            type=ser.validated_data["type"],
            title=ser.validated_data["title"],
            description=ser.validated_data.get("description", ""),
            original_price=ser.validated_data["original_price"],
            sale_price=ser.validated_data["sale_price"],
            is_suspended_meal_eligible=ser.validated_data.get(
                "is_suspended_meal_eligible",
                False,
            ),
        )
        if image := ser.validated_data.get("image"):
            template.image_url = store_uploaded_file(image, prefix="business/templates")
        template.save()
        template.dietary_tags.set(ser.validated_data.get("dietary_tags", []))
        template.allergen_warnings.set(ser.validated_data.get("allergen_warnings", []))
        return Response(BagTemplateSerializer(template).data, status=status.HTTP_201_CREATED)


class BagTemplateDetailView(APIView):
    permission_classes = BUSINESS_PERMISSIONS

    def delete(self, request, pk: str):
        template = get_object_or_404(BagTemplate, pk=pk, business__owner=request.user)
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActiveOrdersView(APIView):
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
    permission_classes = BUSINESS_PERMISSIONS

    def get(self, request, pk: str):
        owned = _owned_location_ids(request.user)
        try:
            order = Order.objects.select_related(
                "bag",
                "consumer__consumer_profile",
                "business_location",
            ).get(pk=pk, business_location_id__in=owned)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(BusinessOrderSerializer(order).data)


class ConfirmPickupByScanView(APIView):
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


class ActiveSuspendedView(APIView):
    permission_classes = BUSINESS_PERMISSIONS

    def get(self, request):
        owned = _owned_location_ids(request.user)
        qs = (
            SuspendedMealDonation.objects.filter(status=DonationStatus.ACTIVE)
            .filter(Q(bag__business_location_id__in=owned) | Q(bag__isnull=True))
            .select_related("bag__business_location")
            .order_by("-created_at")
        )
        return Response(SuspendedMealForDispatchSerializer(qs, many=True).data)


class DispatchSuspendedView(APIView):
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
    permission_classes = BUSINESS_PERMISSIONS

    def get(self, request):
        owned = _owned_location_ids(request.user)
        empty = {
            "active_orders_count": 0,
            "today_completed_count": 0,
            "suspended_meals_available": 0,
            "today_orders_count": 0,
            "today_revenue": Decimal("0.00"),
            "today_bags_sold": 0,
        }
        if not owned:
            return Response(DashboardSummarySerializer(empty).data)

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        active_orders_count = Order.objects.filter(
            business_location_id__in=owned,
            status__in=_NON_TERMINAL_FOR_BUSINESS,
        ).count()
        completed_today = Order.objects.filter(
            business_location_id__in=owned,
            status=OrderStatus.COMPLETED,
            picked_up_at__gte=today_start,
        )
        today_completed_count = completed_today.count()
        metrics = completed_today.aggregate(
            today_revenue=Sum("total_paid"),
            today_bags_sold=Sum("quantity"),
        )
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
                    "today_orders_count": today_completed_count,
                    "today_revenue": metrics["today_revenue"] or Decimal("0.00"),
                    "today_bags_sold": metrics["today_bags_sold"] or 0,
                }
            ).data
        )


def _point(location: BusinessLocation) -> dict[str, float | None]:
    raw = location.location
    if raw is None:
        return {"lat": None, "lng": None}
    if hasattr(raw, "y"):
        return {"lat": raw.y, "lng": raw.x}
    if isinstance(raw, dict):
        return {"lat": raw.get("lat"), "lng": raw.get("lng")}
    return {"lat": None, "lng": None}
