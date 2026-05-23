"""Badges, levels, referrals."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import TimestampedModel


class BadgeCategory(models.TextChoices):
    SAVER = "saver", "Saver"
    STREAK = "streak", "Streak"
    COMMUNITY = "community", "Community"
    EXPLORER = "explorer", "Explorer"
    PREMIUM = "premium", "Premium"


class BadgeRarity(models.TextChoices):
    COMMON = "common", "Common"
    RARE = "rare", "Rare"
    EPIC = "epic", "Epic"
    LEGENDARY = "legendary", "Legendary"


class Badge(TimestampedModel):
    name = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=255)
    icon_url = models.URLField(blank=True)
    category = models.CharField(max_length=20, choices=BadgeCategory.choices, db_index=True)
    rarity = models.CharField(
        max_length=12, choices=BadgeRarity.choices, default=BadgeRarity.COMMON
    )
    criteria = models.JSONField(
        default=dict, blank=True, help_text='e.g. {"meals_saved": 10, "category": "bakery"}'
    )

    class Meta:
        ordering = ["category", "name"]

    def __str__(self) -> str:
        return self.name


class UserBadge(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_badges"
    )
    badge = models.ForeignKey(Badge, on_delete=models.PROTECT, related_name="awards")
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-earned_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="uniq_user_badge"),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} → {self.badge.name}"


class LevelName(models.TextChoices):
    BRONCE = "bronce", "Bronce"
    PLATA = "plata", "Plata"
    ORO = "oro", "Oro"
    COTOPAXI = "cotopaxi", "Cotopaxi"
    GALAPAGOS = "galapagos", "Galápagos"


class UserLevel(TimestampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="level"
    )
    level_name = models.CharField(
        max_length=12, choices=LevelName.choices, default=LevelName.BRONCE
    )
    xp_total = models.PositiveIntegerField(default=0)
    meals_rescued = models.PositiveIntegerField(default=0)
    kg_saved = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    co2_saved_kg = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    money_saved_usd = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    current_streak_weeks = models.PositiveSmallIntegerField(default=0)
    longest_streak_weeks = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "User level"
        ordering = ["-xp_total"]

    def __str__(self) -> str:
        return f"{self.user.email} · {self.level_name} ({self.xp_total} XP)"


class ReferralStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"


class Referral(TimestampedModel):
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="referrals_sent"
    )
    referred = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="referral_record"
    )
    status = models.CharField(
        max_length=12, choices=ReferralStatus.choices, default=ReferralStatus.PENDING
    )
    reward_credit_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Referral<{self.referrer.email} → {self.referred.email}>"
