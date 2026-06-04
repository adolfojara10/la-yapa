"""PayPhone provider.

REST integration based on PayPhone's documented "Cashier Button" / "Web SDK"
hosted-checkout flow:
    POST {base_url}/api/button/Prepare    creates a payment session, returns
                                          a payWithCard URL we redirect to.
    POST {base_url}/api/button/Confirm    we never call this directly — the
                                          consumer hits it from the WebView.
    POST {base_url}/api/Sale/Cancel       refund / void.

Webhook signature: PayPhone signs the payload body with HMAC-SHA256 using
the per-merchant webhook secret and supplies it in `X-PayPhone-Signature`.
A `X-PayPhone-Timestamp` header (unix seconds) lets us reject replays.

⚠️ No real PayPhone sandbox account is provisioned (see checklist.md
Session 8). The fake provider routes all test traffic; this class is
exercised by unit tests with `requests` mocked. First real-money call
will be the first time the actual response shape is validated against
real PayPhone — known caveat, documented in PROGRESS.md.
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

SIGNATURE_HEADER = "X-PayPhone-Signature"
TIMESTAMP_HEADER = "X-PayPhone-Timestamp"


class PayPhoneProvider(PaymentProviderBase):
    name = "payphone"

    def __init__(self) -> None:
        self.api_key = getattr(settings, "PAYPHONE_API_KEY", "")
        self.secret = getattr(settings, "PAYPHONE_SECRET", "")
        self.webhook_secret = getattr(settings, "PAYPHONE_WEBHOOK_SECRET", "")
        self.base_url = getattr(
            settings, "PAYPHONE_BASE_URL", "https://pay.payphonetodoesposible.com"
        )
        if not self.api_key:
            raise ProviderConfigError("PAYPHONE_API_KEY not set")

    # ----- charge ---------------------------------------------------------

    def create_charge(self, order, *, return_url: str) -> ChargeSession:
        # PayPhone amounts are in cents; we'd rather hand them the integer
        # to avoid float/decimal rounding ambiguity.
        amount_cents = int((order.total_paid * 100).quantize(Decimal("1")))
        payload = {
            "amount": amount_cents,
            "amountWithoutTax": amount_cents,
            "currency": "USD",
            "clientTransactionId": str(order.id),
            "responseUrl": return_url,
            "cancellationUrl": return_url,
            "reference": f"Order {order.id}",
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/button/Prepare",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise ProviderError(f"PayPhone Prepare failed: {exc}") from exc

        # PayPhone returns `paymentId` + `payWithPayPhone` URL. Field names
        # have varied across their API versions; defensive lookup.
        provider_tx = str(data.get("paymentId") or data.get("PaymentId") or "")
        webview_url = (
            data.get("payWithPayPhone") or data.get("payWithCard") or data.get("redirectUrl", "")
        )
        if not provider_tx or not webview_url:
            raise ProviderError(f"PayPhone Prepare returned no session: {data}")

        return ChargeSession(
            session_id=provider_tx,
            provider_transaction_id=provider_tx,
            amount=order.total_paid,
            webview_url=webview_url,
            sdk_payload={},
        )

    # ----- refund ---------------------------------------------------------

    def refund(self, *, provider_transaction_id: str, amount: Decimal) -> RefundResult:
        amount_cents = int((amount * 100).quantize(Decimal("1")))
        try:
            response = requests.post(
                f"{self.base_url}/api/Sale/Cancel",
                json={"id": provider_transaction_id, "amount": amount_cents},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=15,
            )
        except requests.RequestException as exc:
            raise RefundFailedError(f"PayPhone refund network error: {exc}") from exc

        if response.status_code >= 400:
            raise RefundFailedError(
                f"PayPhone refund returned {response.status_code}: {response.text[:200]}"
            )
        try:
            data = response.json()
        except ValueError:
            data = {}
        status = "success" if data.get("status") == "Approved" else "pending"
        return RefundResult(
            refund_provider_transaction_id=str(data.get("transactionId") or data.get("id") or ""),
            status=status,
            raw_response=data,
        )

    # ----- webhook --------------------------------------------------------

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
            raise ProviderError("PayPhone webhook body not valid JSON") from exc

        ts_header = headers.get(TIMESTAMP_HEADER) or headers.get(TIMESTAMP_HEADER.lower())
        try:
            sent_at = int(ts_header) if ts_header else int(time.time())
        except (TypeError, ValueError):
            sent_at = int(time.time())

        # PayPhone webhook field naming is provider-version-dependent.
        # We accept both camelCase and PascalCase keys defensively.
        event_id = str(payload.get("eventId") or payload.get("EventId") or "")
        event_status = (payload.get("status") or payload.get("Status") or "").lower()
        provider_tx = str(payload.get("paymentId") or payload.get("PaymentId") or "")
        raw_amount = payload.get("amount") or payload.get("Amount")
        amount = Decimal(str(raw_amount) if raw_amount is not None else "0") / Decimal("100")

        event_type = {
            "approved": "payment.succeeded",
            "captured": "payment.succeeded",
            "rejected": "payment.failed",
            "cancelled": "payment.failed",
            "refunded": "refund.succeeded",
            "refundfailed": "refund.failed",
        }.get(event_status, f"payment.{event_status or 'unknown'}")

        return WebhookEvent(
            event_id=event_id or f"payphone-{provider_tx}-{sent_at}",
            event_type=event_type,
            provider_transaction_id=provider_tx,
            amount=amount,
            age_seconds=max(0, int(time.time()) - sent_at),
            raw=payload,
        )
