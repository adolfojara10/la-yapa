"""User registration: email/password and social."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.users.models import ConsumerProfile, User

from . import email_otp


@dataclass
class RegisterResult:
    user: User
    created: bool  # False when social-auth find-or-create returned an existing user


@transaction.atomic
def register_email_user(
    *,
    email: str,
    password: str,
    role: str = User.Role.CONSUMER,
    first_name: str = "",
    last_name: str = "",
    send_verification: bool = True,
) -> RegisterResult:
    """Create a fresh email/password user, attach the role-appropriate profile,
    and (by default) send a verification OTP. Caller is responsible for
    catching IntegrityError on duplicate email — typically the serializer
    already validated uniqueness."""
    if role not in {User.Role.CONSUMER, User.Role.BUSINESS_OWNER}:
        raise ValueError(f"Self-signup not allowed for role={role!r}")

    user = User.objects.create_user(
        username=email,  # AbstractUser requires a unique username; mirror email
        email=email,
        password=password,
        role=role,
        first_name=first_name,
        last_name=last_name,
    )
    _attach_profile(user)
    if send_verification:
        email_otp.issue_and_send(user)
    return RegisterResult(user=user, created=True)


@transaction.atomic
def get_or_create_social_user(
    *,
    email: str,
    first_name: str = "",
    last_name: str = "",
    email_verified: bool = True,
) -> RegisterResult:
    """Find a user by email (case-insensitive) or create a new consumer.
    Social-auth providers (Google, Apple) only support consumer signup —
    business accounts must come through the explicit business onboarding flow.
    """
    email = email.strip().lower()
    try:
        user = User.objects.get(email__iexact=email)
        created = False
        if email_verified and not user.is_email_verified:
            from django.utils import timezone

            user.is_email_verified = True
            user.email_verified_at = timezone.now()
            user.save(update_fields=["is_email_verified", "email_verified_at", "updated_at"])
        if not user.first_name and first_name:
            user.first_name = first_name
            user.save(update_fields=["first_name", "updated_at"])
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=email,
            email=email,
            role=User.Role.CONSUMER,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_unusable_password()
        if email_verified:
            from django.utils import timezone

            user.is_email_verified = True
            user.email_verified_at = timezone.now()
        user.save()
        _attach_profile(user)
        created = True

    return RegisterResult(user=user, created=created)


def _attach_profile(user: User) -> None:
    """Create the role-appropriate profile row.

    Consumers get a ConsumerProfile. Business owners do NOT get a profile here:
    the business itself is created later through the business-onboarding wizard
    (Phase 2 of the master roadmap), which collects RUC/cédula and food-safety
    acceptance. Until then, the User row alone is enough for them to log in.
    """
    if user.role == User.Role.CONSUMER:
        ConsumerProfile.objects.get_or_create(
            user=user,
            defaults={"first_name": user.first_name, "last_name": user.last_name},
        )
