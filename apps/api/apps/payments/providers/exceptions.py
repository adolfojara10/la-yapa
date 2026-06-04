"""Provider-layer exceptions, surfaced upward to the webhook + service layer."""

from __future__ import annotations


class ProviderError(Exception):
    """Generic provider-side failure (network, 5xx, malformed response)."""

    code: str = "provider_error"

    def __init__(self, message: str = "", *, code: str | None = None):
        super().__init__(message or self.code)
        if code:
            self.code = code


class ProviderConfigError(ProviderError):
    """Required env vars (api key / secret) not set."""

    code = "provider_misconfigured"


class SignatureInvalidError(ProviderError):
    """HMAC signature mismatch on an incoming webhook."""

    code = "invalid_signature"


class WebhookReplayError(ProviderError):
    """Webhook event timestamp outside the accepted window."""

    code = "replay_window_exceeded"


class RefundFailedError(ProviderError):
    """Provider refused or failed the refund call."""

    code = "refund_failed"
