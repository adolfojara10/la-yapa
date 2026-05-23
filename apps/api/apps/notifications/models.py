"""NotificationPreference + PushToken (Expo)."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.core.models import TimestampedModel


class NotificationPreference(TimestampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preference"
    )
    favorite_business_new_bags = models.BooleanField(default=True)
    last_minute_deals = models.BooleanField(default=True)
    pickup_reminders = models.BooleanField(default=True)
    order_updates = models.BooleanField(default=True)
    achievements = models.BooleanField(default=True)
    marketing = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Notification preference"
        verbose_name_plural = "Notification preferences"

    def __str__(self) -> str:
        return f"NotifPrefs<{self.user.email}>"


class PushPlatform(models.TextChoices):
    IOS = "ios", "iOS"
    ANDROID = "android", "Android"


class PushToken(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_tokens"
    )
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=10, choices=PushPlatform.choices)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Push<{self.platform}:{self.user.email}>"
