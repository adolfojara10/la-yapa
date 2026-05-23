"""User + ConsumerProfile + DietaryTag."""

from __future__ import annotations

import secrets
import string

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimestampedModel
from apps.geo.fields import PointField


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
