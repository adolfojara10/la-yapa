"""Abstract payment provider interface.

Every concrete provider (PayPhone, DeUna, future Stripe) returns the same
shape from `create_charge` so the mobile + view layer stays provider-agnostic.

`ChargeSession` carries either:
  - `webview_url`   The provider hosts the form; mobile opens it in expo-web-browser.
  - `sdk_payload`   Forward-compat for the Phase 2 native-SDK migration. Empty
                    dict today (no provider returns SDK payloads this session).

Webhook handling splits into `verify_signature` (pure crypto, no DB) and
`parse_event` (translates the provider's payload into our normalized
`WebhookEvent`). The dispatcher in `apps.payments.webhooks` calls both.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class ChargeSession:
    """Returned by `create_charge`. Mobile uses one of webview_url / sdk_payload."""

    session_id: str
    provider_transaction_id: str
    amount: Decimal
    currency: str = "USD"
    webview_url: str = ""
    sdk_payload: dict[str, Any] = field(default_factory=dict)
    expires_in_seconds: int = 600


@dataclass
class RefundResult:
    refund_provider_transaction_id: str
    status: str  # "pending" | "success" | "failed"
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookEvent:
    """Normalized webhook payload — what the dispatcher acts on."""

    event_id: str
    event_type: str  # "payment.succeeded" | "payment.failed" | "refund.succeeded" | "refund.failed"
    provider_transaction_id: str
    amount: Decimal | None
    age_seconds: int  # used for replay-window check
    raw: dict[str, Any]


class PaymentProviderBase(ABC):
    """Concrete providers implement these four methods."""

    name: str = ""  # set by subclass

    @abstractmethod
    def create_charge(self, order, *, return_url: str) -> ChargeSession:
        """Create a charge session at the provider, return the redirect URL."""

    @abstractmethod
    def refund(self, *, provider_transaction_id: str, amount: Decimal) -> RefundResult:
        """Request a refund. Result may be pending (async settlement) or
        immediate (synchronous failure)."""

    @abstractmethod
    def verify_signature(self, raw_body: bytes, headers: dict[str, str]) -> bool:
        """Return True iff the HMAC over `raw_body` matches the provider's
        signing key. Constant-time compare."""

    @abstractmethod
    def parse_event(self, raw_body: bytes, headers: dict[str, str]) -> WebhookEvent:
        """Translate a verified webhook payload into our normalized shape."""
