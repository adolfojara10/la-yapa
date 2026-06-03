"""User + ConsumerProfile + DietaryTag + email/password auth tokens."""

from __future__ import annotations

import hashlib
import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from apps.core.models import TimestampedModel
from apps.geo.fields import PointField


def _generate_otp_code(length: int = 6) -> str:
    """Cryptographically random numeric code, zero-padded."""
    upper = 10**length
    return str(secrets.randbelow(upper)).zfill(length)


def _generate_password_reset_token() -> str:
    """URL-safe opaque token; the raw value is shown once (in email),
    only the SHA-256 hash is persisted."""
    return secrets.token_urlsafe(48)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _generate_referral_code(length: int = 7) -> str:
    """URL-friendly uppercase referral code, e.g. 'YAPA7K3'."""
    alphabet = string.ascii_uppercase + string.digits
    return "YAPA" + "".join(secrets.choice(alphabet) for _ in range(length - 4))


class User(AbstractUser):
    """La Yapa user. Email is the canonical identifier."""

    class Role(models.TextChoices):
        CONSUMER = "consumer", "Consumer"
        BUSINESS_OWNER = "business_owner", "Business Owner"
        ADMIN = "admin", "Admin"
        SALES_REP = "sales_rep", "Sales Rep"

    class Language(models.TextChoices):
        SPANISH = "es", "Español"
        ENGLISH = "en", "English"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CONSUMER)
    language = models.CharField(max_length=5, choices=Language.choices, default=Language.SPANISH)

    is_email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    is_premium = models.BooleanField(default=False)
    premium_expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["role"])]

    def __str__(self) -> str:
        return self.email


class DietaryTag(TimestampedModel):
    """Vegetarian / vegan / gluten_free / etc. Used by ConsumerProfile and Bag."""

    name = models.CharField(max_length=40, unique=True)
    label_es = models.CharField(max_length=80)
    label_en = models.CharField(max_length=80, blank=True)
    icon_name = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Dietary tag"
        verbose_name_plural = "Dietary tags"

    def __str__(self) -> str:
        return self.label_es or self.name


class ConsumerProfile(TimestampedModel):
    """Profile for users with role=consumer."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="consumer_profile")
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    avatar_url = models.URLField(blank=True)

    default_location = PointField(null=True, blank=True)
    default_address = models.CharField(max_length=255, blank=True)

    dietary_preferences = models.ManyToManyField(DietaryTag, blank=True, related_name="consumers")
    notifications_settings = models.JSONField(default=dict, blank=True)

    referral_code = models.CharField(max_length=12, unique=True, default=_generate_referral_code)
    referred_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals_made",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Consumer profile"
        verbose_name_plural = "Consumer profiles"

    def __str__(self) -> str:
        return f"Profile<{self.user.email}>"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = _generate_referral_code()
        super().save(*args, **kwargs)

    @property
    def onboarding_completed(self) -> bool:
        """A consumer has finished onboarding once they've given us a first
        name AND picked at least one dietary preference. Location permission
        is tracked client-side (we just record default_location if granted)."""
        if not self.first_name:
            return False
        return self.dietary_preferences.exists()


class EmailVerificationCode(TimestampedModel):
    """Short-lived 6-digit OTP for email verification.

    A user may have multiple historical codes; the most recent unconsumed,
    unexpired one wins. `attempts` is bumped on every failed match to a
    given code; over EMAIL_VERIFICATION_MAX_ATTEMPTS it is forcibly consumed.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="email_verification_codes"
    )
    code = models.CharField(max_length=6, default=_generate_otp_code)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "consumed_at"]),
        ]
        verbose_name = "Email verification code"
        verbose_name_plural = "Email verification codes"

    def __str__(self) -> str:
        state = "used" if self.consumed_at else ("expired" if self.is_expired else "active")
        return f"OTP<{self.user.email} {state}>"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None

    def mark_consumed(self) -> None:
        self.consumed_at = timezone.now()
        self.save(update_fields=["consumed_at", "updated_at"])

    @classmethod
    def issue(cls, user: User) -> EmailVerificationCode:
        """Create a fresh code for `user` and invalidate any unconsumed prior codes."""
        cls.objects.filter(user=user, consumed_at__isnull=True).update(consumed_at=timezone.now())
        ttl = timedelta(minutes=settings.EMAIL_VERIFICATION_OTP_TTL_MINUTES)
        return cls.objects.create(user=user, expires_at=timezone.now() + ttl)


class PasswordResetToken(TimestampedModel):
    """Single-use password-reset token. Raw value is delivered via email;
    only its SHA-256 hash is stored, so the DB never sees the plaintext.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Password reset token"
        verbose_name_plural = "Password reset tokens"

    def __str__(self) -> str:
        state = "used" if self.consumed_at else ("expired" if self.is_expired else "active")
        return f"Reset<{self.user.email} {state}>"

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None

    def mark_consumed(self) -> None:
        self.consumed_at = timezone.now()
        self.save(update_fields=["consumed_at", "updated_at"])

    @classmethod
    def issue(cls, user: User) -> tuple[PasswordResetToken, str]:
        """Create a new token and return (instance, raw_token).
        Caller is responsible for emailing the raw value — it cannot be recovered later.
        Any unconsumed prior tokens for the user are invalidated."""
        cls.objects.filter(user=user, consumed_at__isnull=True).update(consumed_at=timezone.now())
        raw = _generate_password_reset_token()
        ttl = timedelta(minutes=settings.PASSWORD_RESET_TOKEN_TTL_MINUTES)
        instance = cls.objects.create(
            user=user,
            token_hash=_hash_token(raw),
            expires_at=timezone.now() + ttl,
        )
        return instance, raw

    @classmethod
    def find_valid(cls, raw: str) -> PasswordResetToken | None:
        """Look up a usable token from its raw value, or None."""
        try:
            instance = cls.objects.select_related("user").get(token_hash=_hash_token(raw))
        except cls.DoesNotExist:
            return None
        if instance.is_consumed or instance.is_expired:
            return None
        return instance
