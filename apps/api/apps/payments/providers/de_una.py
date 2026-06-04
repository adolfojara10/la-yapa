"""DeUna provider — hosted-checkout WebView only.

DeUna's developer portal exposes a REST API to create payment links:
    POST {base_url}/payment_link    create a one-time payment session.

DeUna webhooks come with `X-DeUna-Signature` (HMAC-SHA256 over body, hex)
and `X-DeUna-Timestamp` (unix seconds). Same shape as PayPhone for the
dispatcher's purposes.

⚠️ Same caveat as PayPhone — no real DeUna sandbox account is provisioned.
Tests run via FakePaymentProvider. First real call validates the response
shape against DeUna's docs. The field names below match DeUna's published
API schema as of writing; defensive lookups handle minor variations.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from decimal import Decimal

import requests
from django.conf import settings

from .base import ChargeSession, PaymentProviderBase, RefundResult, WebhookEvent
from .exceptions import (
    ProviderConfigError,
    ProviderError,
    RefundFailedError,
    SignatureInvalidError,
)

SIGNATURE_HEADER = "X-DeUna-Signature"
TIMESTAMP_HEADER = "X-DeUna-Timestamp"


class DeUnaProvider(PaymentProviderBase):
    name = "de_una"

    def __init__(self) -> None:
        self.public_key = getattr(settings, "DEUNA_PUBLIC_KEY", "")
        self.secret_key = getattr(settings, "DEUNA_SECRET_KEY", "")
        self.webhook_secret = getattr(settings, "DEUNA_WEBHOOK_SECRET", "")
        self.base_url = getattr(settings, "DEUNA_BASE_URL", "https://api.deuna.com/v1")
        if not self.secret_key:
            raise ProviderConfigError("DEUNA_SECRET_KEY not set")

    def create_charge(self, order, *, return_url: str) -> ChargeSession:
        payload = {
            "amount": str(order.total_paid),
            "currency": "USD",
            "description": f"La Yapa · Order {order.id}",
            "external_id": str(order.id),
            "redirect_url": return_url,
        }
        try:
            response = requests.post(
                f"{self.base_url}/payment_link",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.secret_key}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise ProviderError(f"DeUna payment_link failed: {exc}") from exc

        provider_tx = str(data.get("id") or data.get("payment_id") or "")
        webview_url = data.get("checkout_url") or data.get("url", "")
        if not provider_tx or not webview_url:
            raise ProviderError(f"DeUna payment_link returned no session: {data}")

        return ChargeSession(
            session_id=provider_tx,
            provider_transaction_id=provider_tx,
            amount=order.total_paid,
            webview_url=webview_url,
            sdk_payload={},
        )

    def refund(self, *, provider_transaction_id: str, amount: Decimal) -> RefundResult:
        try:
            response = requests.post(
                f"{self.base_url}/payments/{provider_transaction_id}/refunds",
                json={"amount": str(amount)},
                headers={"Authorization": f"Bearer {self.secret_key}"},
                timeout=15,
            )
        except requests.RequestException as exc:
            raise RefundFailedError(f"DeUna refund network error: {exc}") from exc

        if response.status_code >= 400:
            raise RefundFailedError(
                f"DeUna refund returned {response.status_code}: {response.text[:200]}"
            )
        try:
            data = response.json()
        except ValueError:
            data = {}
        status_raw = (data.get("status") or "").lower()
        status = (
            "success"
            if status_raw in {"succeeded", "completed"}
            else ("failed" if status_raw == "failed" else "pending")
        )
        return RefundResult(
            refund_provider_transaction_id=str(data.get("id") or ""),
            status=status,
            raw_response=data,
        )

    def verify_signature(self, raw_body: bytes, headers: dict[str, str]) -> bool:
        if not self.webhook_secret:
            return False
        provided = headers.get(SIGNATURE_HEADER) or headers.get(SIGNATURE_HEADER.lower(), "")
        if not provided:
            return False
        expected = hmac.new(
            self.webhook_secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(provided, expected)

    def parse_event(self, raw_body: bytes, headers: dict[str, str]) -> WebhookEvent:
        if not self.verify_signature(raw_body, headers):
            raise SignatureInvalidError()
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ProviderError("DeUna webhook body not valid JSON") from exc

        ts_header = headers.get(TIMESTAMP_HEADER) or headers.get(TIMESTAMP_HEADER.lower())
        try:
            sent_at = int(ts_header) if ts_header else int(time.time())
        except (TypeError, ValueError):
            sent_at = int(time.time())

        event_id = str(payload.get("event_id") or payload.get("id") or "")
        event_status = (payload.get("status") or "").lower()
        provider_tx = str(payload.get("payment_id") or payload.get("id") or "")
        raw_amount = payload.get("amount")
        try:
            amount = Decimal(str(raw_amount)) if raw_amount is not None else None
        except (TypeError, ArithmeticError):
            amount = None

        event_type = {
            "succeeded": "payment.succeeded",
            "completed": "payment.succeeded",
            "failed": "payment.failed",
            "refunded": "refund.succeeded",
            "refund_failed": "refund.failed",
        }.get(event_status, f"payment.{event_status or 'unknown'}")

        return WebhookEvent(
            event_id=event_id or f"de_una-{provider_tx}-{sent_at}",
            event_type=event_type,
            provider_transaction_id=provider_tx,
            amount=amount,
            age_seconds=max(0, int(time.time()) - sent_at),
            raw=payload,
        )
