"""Order endpoints for consumers: list / detail / create / cancel / redeem-credit."""

from __future__ import annotations

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import CancelledBy, Order
from apps.orders.services import (
    BagUnavailable,
    CancellationNotAllowed,
    CancellationOutsideWindow,
    InsufficientStock,
    OrderServiceError,
    cancel_order,
    create_order,
)
from apps.payments.models import BonusCredit
from apps.payments.services import CreditError, apply_bonus_credit

from .orders_serializers import (
    BonusCreditSerializer,
    CancelOrderSerializer,
    CreateOrderSerializer,
    OrderSerializer,
    RedeemCreditSerializer,
)
from .pagination import BagCursorPagination
from .views import CONSUMER_PERMISSIONS


class OrderListView(GenericAPIView):
    """GET  /api/v1/consumer/orders     consumer's order history
    POST /api/v1/consumer/orders     create a new order (PENDING_PAYMENT)
    """

    permission_classes = CONSUMER_PERMISSIONS
    pagination_class = BagCursorPagination
    serializer_class = OrderSerializer

    def get(self, request):
        qs = Order.objects.filter(consumer=request.user).select_related(
            "bag", "business_location__business"
        )
        paginator = self.pagination_class()
        paginator.ordering = ("-created_at", "id")
        page = paginator.paginate_queryset(qs, request, view=self)
        ser = self.get_serializer(page or qs, many=True)
        if page is not None:
            return paginator.get_paginated_response(ser.data)
        return Response(ser.data)

    def post(self, request):
        ser = CreateOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            order = create_order(
                consumer=request.user,
                bag_id=ser.validated_data["bag_id"],
                quantity=ser.validated_data["quantity"],
                donate_as_suspended_meal=ser.validated_data["donate_as_suspended_meal"],
            )
        except (BagUnavailable, InsufficientStock) as exc:
            return Response(
                {"detail": str(exc), "code": exc.code},
                status=status.HTTP_409_CONFLICT,
            )
        except OrderServiceError as exc:
            return Response(
                {"detail": str(exc), "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(GenericAPIView):
    """GET /api/v1/consumer/orders/{id}"""

    permission_classes = CONSUMER_PERMISSIONS
    serializer_class = OrderSerializer

    def get(self, request, pk):
        try:
            order = Order.objects.select_related("bag", "business_location__business").get(
                pk=pk, consumer=request.user
            )
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)


class OrderCancelView(APIView):
    """POST /api/v1/consumer/orders/{id}/cancel"""

    permission_classes = CONSUMER_PERMISSIONS

    def post(self, request, pk):
        ser = CancelOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            order = Order.objects.get(pk=pk, consumer=request.user)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            result = cancel_order(
                order=order,
                actor=CancelledBy.CONSUMER,
                reason=ser.validated_data.get("reason", ""),
            )
        except CancellationOutsideWindow as exc:
            return Response(
                {"detail": str(exc), "code": exc.code},
                status=status.HTTP_409_CONFLICT,
            )
        except CancellationNotAllowed as exc:
            return Response(
                {"detail": str(exc), "code": exc.code},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {
                "order": OrderSerializer(result.order).data,
                "triggered_refund": result.triggered_refund,
            }
        )


class OrderRedeemCreditView(APIView):
    """POST /api/v1/consumer/orders/{id}/redeem-credit"""

    permission_classes = CONSUMER_PERMISSIONS

    def post(self, request, pk):
        ser = RedeemCreditSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            order = Order.objects.get(pk=pk, consumer=request.user)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            applied = apply_bonus_credit(order=order, credit_id=ser.validated_data["credit_id"])
        except CreditError as exc:
            return Response(
                {"detail": str(exc), "code": exc.code},
                status=status.HTTP_409_CONFLICT,
            )
        order.refresh_from_db()
        return Response(
            {
                "order": OrderSerializer(order).data,
                "applied_credit_amount": str(applied),
            }
        )


class BonusCreditListView(APIView):
    """GET /api/v1/consumer/bonus-credits — list the consumer's active credits."""

    permission_classes = CONSUMER_PERMISSIONS

    def get(self, request):
        credits = BonusCredit.objects.filter(user=request.user).order_by("-created_at")
        return Response(BonusCreditSerializer(credits, many=True).data)
