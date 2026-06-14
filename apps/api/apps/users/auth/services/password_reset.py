"""Password reset request + execution."""

from __future__ import annotations

from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.users.models import PasswordResetToken, User

from .mail import send_templated_email


def request_reset(email: str) -> None:
    """Send a password-reset email if an account with `email` exists.

    Always silent on the user lookup — we never reveal whether an email is
    registered. Caller (view) returns 200 unconditionally.
    """
    email = (email or "").strip().lower()
    if not email:
        return
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return

    web_link, mobile_link = issue_reset_links(user)

    send_templated_email(
        to=user.email,
        subject_es="Restablecer tu contraseña · La Yapa",
        subject_en="Reset your password · La Yapa",
        template_base="emails/password_reset",
        context={
            "user": user,
            "web_link": web_link,
            "mobile_link": mobile_link,
            "ttl_minutes": settings.PASSWORD_RESET_TOKEN_TTL_MINUTES,
        },
        language=user.language,
    )


def issue_reset_links(user: User) -> tuple[str, str]:
    """Return fresh (web_link, mobile_link) reset URLs for `user`."""

    _, raw_token = PasswordResetToken.issue(user)
    web_link = f"{settings.FRONTEND_URL}/reset-password?{urlencode({'token': raw_token})}"
    mobile_link = (
        f"{settings.MOBILE_DEEP_LINK_SCHEME}://reset-password?{urlencode({'token': raw_token})}"
    )
    return web_link, mobile_link


class ResetError(Exception):
    """Raised when reset cannot complete. `.reason` is a stable code for the API."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(detail or reason)
        self.reason = reason
        self.detail = detail


def perform_reset(*, raw_token: str, new_password: str) -> User:
    """Validate the token and update the user's password. Single-use."""
    if not raw_token or not new_password:
        raise ResetError("invalid_token")

    instance = PasswordResetToken.find_valid(raw_token)
    if instance is None:
        raise ResetError("invalid_token")

    user = instance.user
    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise ResetError("weak_password", "; ".join(exc.messages)) from exc

    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    instance.mark_consumed()
    return user
