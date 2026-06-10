"""Payment views — charge initiation + provider webhooks."""

from __future__ import annotations

import json
import logging
import uuid
from urllib.parse import urlencode

from django.http import HttpResponse
from django.test import RequestFactory
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from apps.payments.models import PaymentTransaction
from apps.payments.providers.fake import FakePaymentProvider
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


class FakeCheckoutView(APIView):
    """Local dev view: interactive UI to simulate fake payment success/failure."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request, tx_id):
        return_url = request.query_params.get("return", "")
        status_val = request.query_params.get("status", "")

        if status_val:
            if status_val in ("success", "failure"):
                try:
                    tx = PaymentTransaction.objects.get(provider_transaction_id=tx_id)
                    event_type = (
                        "payment.succeeded" if status_val == "success" else "payment.failed"
                    )
                    payload = {
                        "id": f"evt-{uuid.uuid4().hex[:8]}",
                        "type": event_type,
                        "transaction_id": tx_id,
                        "amount": str(tx.amount),
                    }
                    body = json.dumps(payload).encode("utf-8")
                    headers = FakePaymentProvider.sign(payload)

                    rf = RequestFactory()
                    mock_request = rf.post(
                        "/api/v1/payments/fake/webhook",
                        data=body,
                        content_type="application/json",
                    )
                    for k, v in headers.items():
                        mock_request.META[f"HTTP_{k.upper().replace('-', '_')}"] = v

                    handle_webhook_request(provider_name=tx.provider, request=mock_request)
                except Exception:
                    logger.exception("Failed to dispatch fake webhook")

            response = HttpResponse("", status=302)
            response["Location"] = return_url
            return response

        success_url = f"{request.path}?{urlencode({'return': return_url, 'status': 'success'})}"
        fail_url = f"{request.path}?{urlencode({'return': return_url, 'status': 'failure'})}"

        html = f"""
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px; padding: 20px;">
            <h2>Fake Payment Checkout</h2>
            <p>Transaction: <code>{tx_id}</code></p>
            <p>Click below to simulate the provider webhook.</p>
            <a href="{success_url}" style="display: block; padding: 15px; background: #16a34a; color: white; font-size: 18px; text-decoration: none; border-radius: 8px; width: 100%; margin-bottom: 20px; box-sizing: border-box;">Simulate Success</a>
            <a href="{fail_url}" style="display: block; padding: 15px; background: #dc2626; color: white; font-size: 18px; text-decoration: none; border-radius: 8px; width: 100%; box-sizing: border-box;">Simulate Failure</a>
        </body>
        </html>
        """
        return HttpResponse(html)
