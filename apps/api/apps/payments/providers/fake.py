"""Deterministic test-double payment provider.

Active when `settings.USE_FAKE_PAYMENT_PROVIDER = True` (test settings,
optionally dev when real keys aren't set). Behavior is fully synchronous:
charges succeed unless `amount == FORCED_FAILURE_AMOUNT`, refunds always
succeed unless flagged.

Webhook signatures use a fixed HMAC key so test cases can sign payloads
deterministically without env shenanigans.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from decimal import Decimal

from django.conf import settings

from .base import ChargeSession, PaymentProviderBase, RefundResult, WebhookEvent
from .exceptions import SignatureInvalidError

FAKE_SIGNING_KEY = b"fake-payment-signing-key-do-not-use-in-prod"
FORCED_FAILURE_AMOUNT = Decimal("66.66")
SIGNATURE_HEADER = "X-Layapa-Fake-Signature"


def _hmac_hex(payload: bytes) -> str:
    return hmac.new(FAKE_SIGNING_KEY, payload, hashlib.sha256).hexdigest()


class FakePaymentProvider(PaymentProviderBase):
    def __init__(self, name: str = "fake") -> None:
        # Take the requested real provider name so PaymentTransaction rows
        # stored under tests still match the routing key.
        self.name = name

    def create_charge(self, order, *, return_url: str) -> ChargeSession:
        if order.total_paid == FORCED_FAILURE_AMOUNT:
            raise SignatureInvalidError("Fake provider forced failure (test hook)")
        tx_id = f"fake-tx-{uuid.uuid4().hex[:12]}"
        return ChargeSession(
            session_id=f"fake-session-{uuid.uuid4().hex[:8]}",
            provider_transaction_id=tx_id,
            amount=order.total_paid,
            webview_url=f"{settings.FAKE_PAYMENT_BASE_URL}/api/v1/payments/fake/checkout/{tx_id}?return={return_url}",
            sdk_payload={},
        )

    def refund(self, *, provider_transaction_id: str, amount: Decimal) -> RefundResult:
        # In the fake, refund is instant + always succeeds.
        return RefundResult(
            refund_provider_transaction_id=f"fake-rfd-{uuid.uuid4().hex[:12]}",
            status="success",
            raw_response={"refunded": str(amount), "tx": provider_transaction_id},
        )

    def verify_signature(self, raw_body: bytes, headers: dict[str, str]) -> bool:
        provided = headers.get(SIGNATURE_HEADER) or headers.get(SIGNATURE_HEADER.lower())
        if not provided:
            return False
        expected = _hmac_hex(raw_body)
        return hmac.compare_digest(provided, expected)

    def parse_event(self, raw_body: bytes, headers: dict[str, str]) -> WebhookEvent:
        if not self.verify_signature(raw_body, headers):
            raise SignatureInvalidError()
        payload = json.loads(raw_body.decode("utf-8"))
        amount = payload.get("amount")
        return WebhookEvent(
            event_id=payload["id"],
            event_type=payload["type"],
            provider_transaction_id=payload["transaction_id"],
            amount=Decimal(str(amount)) if amount is not None else None,
            age_seconds=max(0, int(time.time()) - int(payload.get("created_at", time.time()))),
            raw=payload,
        )

    # ---- test-only helpers (used by webhook tests) ----

    @staticmethod
    def sign(payload: dict) -> dict[str, str]:
        body = json.dumps(payload).encode("utf-8")
        return {SIGNATURE_HEADER: _hmac_hex(body)}
