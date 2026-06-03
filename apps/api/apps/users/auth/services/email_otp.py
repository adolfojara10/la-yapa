"""Email OTP issuance + verification."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

from apps.users.models import EmailVerificationCode, User

from .mail import send_templated_email


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    reason: str = ""  # 'invalid' | 'expired' | 'too_many_attempts'


def issue_and_send(user: User) -> EmailVerificationCode:
    """Create a fresh OTP for `user` and email it. Returns the persisted code
    instance (the raw `code` is on the instance — caller may inspect for testing,
    but normal callers never need it once the email is sent)."""
    code = EmailVerificationCode.issue(user)
    send_templated_email(
        to=user.email,
        subject_es="Tu código de verificación · La Yapa",
        subject_en="Your verification code · La Yapa",
        template_base="emails/verification_code",
        context={"user": user, "code": code.code, "ttl_minutes": code.expires_at},
        language=user.language,
    )
    return code


def verify(user: User, raw_code: str) -> VerifyResult:
    """Validate an OTP. Marks the user verified on success."""
    raw_code = (raw_code or "").strip()
    if not raw_code:
        return VerifyResult(False, "invalid")

    latest = (
        EmailVerificationCode.objects.filter(user=user, consumed_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if latest is None:
        return VerifyResult(False, "invalid")

    if latest.is_expired:
        latest.mark_consumed()
        return VerifyResult(False, "expired")

    if latest.attempts >= settings.EMAIL_VERIFICATION_MAX_ATTEMPTS:
        latest.mark_consumed()
        return VerifyResult(False, "too_many_attempts")

    if latest.code != raw_code:
        latest.attempts += 1
        update_fields = ["attempts", "updated_at"]
        if latest.attempts >= settings.EMAIL_VERIFICATION_MAX_ATTEMPTS:
            latest.consumed_at = timezone.now()
            update_fields.append("consumed_at")
        latest.save(update_fields=update_fields)
        return VerifyResult(False, "invalid")

    latest.mark_consumed()
    if not user.is_email_verified:
        user.is_email_verified = True
        user.email_verified_at = timezone.now()
        user.save(update_fields=["is_email_verified", "email_verified_at", "updated_at"])
        # Send welcome email on the first successful verification.
        send_templated_email(
            to=user.email,
            subject_es="¡Bienvenido a La Yapa! 🌱",
            subject_en="Welcome to La Yapa! 🌱",
            template_base="emails/welcome",
            context={"user": user},
            language=user.language,
        )
    return VerifyResult(True)


# Re-exported for tests that want to assert a rendered subject string.
def render_verification_subject(language: str) -> str:
    return render_to_string(
        f"emails/verification_code.{language}.subject.txt",
        {},
    ).strip()
