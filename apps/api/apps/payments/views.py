"""Payment views — charge initiation + provider webhooks."""

from __future__ import annotations

import logging

from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from apps.users.auth.permissions import ConsumerOnly, IsEmailVerified

from .services import PaymentError, process_payment
from .webhooks import WebhookRejected, handle_webhook_request

logger = logging.getLogger(__name__)


class ChargeSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider = serializers.ChoiceField(choices=["payphone", "de_una"])
    # CharField (not URLField) because we accept mobile deep-link schemes
    # like `layapa://payment-result` which DRF's URLField rejects.
    return_url = serializers.CharField(max_length=512)


class ChargeView(APIView):
    """POST /api/v1/payments/charge — create a payment session.

    Returns a webview URL the mobile client opens in expo-web-browser.
    The webhook is authoritative — even if the WebView reports success,
    UI shows "Procesando" until the order status flips via webhook.
    """

    permission_classes = [IsAuthenticated, ConsumerOnly, IsEmailVerified]

    def post(self, request):
        ser = ChargeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            order = Order.objects.get(pk=ser.validated_data["order_id"], consumer=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            ctx = process_payment(
                order=order,
                provider_name=ser.validated_data["provider"],
                return_url=ser.validated_data["return_url"],
            )
        except PaymentError as exc:
            return Response(
                {"detail": str(exc), "code": exc.code}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "session_id": ctx.session.session_id,
                "provider": ser.validated_data["provider"],
                "webview_url": ctx.session.webview_url,
                "sdk_payload": ctx.session.sdk_payload,
                "amount": str(ctx.session.amount),
                "currency": ctx.session.currency,
                "transaction_id": ctx.transaction.id,
            },
            status=status.HTTP_201_CREATED,
        )


class _WebhookView(APIView):
    """Base for provider webhook endpoints. Subclass sets `provider_name`."""

    permission_classes = [AllowAny]
    authentication_classes: list = []  # webhooks come unauthenticated; HMAC is the proof.
    provider_name: str = ""

    def post(self, request):
        try:
            handle_webhook_request(provider_name=self.provider_name, request=request)
        except WebhookRejected:
            # Same response for all rejection reasons — no leak.
            return Response({"detail": "rejected"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            logger.exception("Unexpected webhook handler error (%s)", self.provider_name)
            return Response({"detail": "internal"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_200_OK)


class PayPhoneWebhookView(_WebhookView):
    provider_name = "payphone"


class DeUnaWebhookView(_WebhookView):
    provider_name = "de_una"
