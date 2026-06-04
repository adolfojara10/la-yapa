"""Payment provider registry.

`get_provider(name)` is the single boundary between service code and
provider-specific HTTP. Providers are looked up by their `PaymentProvider`
choice string ("payphone", "de_una", ...). The fake provider is wired in
under the same registry when settings.USE_FAKE_PAYMENT_PROVIDER is True
(set by test settings).
"""

from __future__ import annotations

from django.conf import settings

from .base import PaymentProviderBase
from .de_una import DeUnaProvider
from .fake import FakePaymentProvider
from .payphone import PayPhoneProvider


def get_provider(name: str) -> PaymentProviderBase:
    """Resolve a provider name to a configured instance."""
    if getattr(settings, "USE_FAKE_PAYMENT_PROVIDER", False):
        # In tests + local dev without real credentials, route everything
        # through the deterministic fake. Real provider classes still
        # importable for type-checking.
        return FakePaymentProvider(name=name)

    if name == "payphone":
        return PayPhoneProvider()
    if name == "de_una":
        return DeUnaProvider()
    raise ValueError(f"Unknown payment provider {name!r}")


__all__ = [
    "PaymentProviderBase",
    "PayPhoneProvider",
    "DeUnaProvider",
    "FakePaymentProvider",
    "get_provider",
]
