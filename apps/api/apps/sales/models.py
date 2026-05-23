"""SalesRepProfile (Phase 2)."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.businesses.models import Business
from apps.core.models import TimestampedModel


class SalesRepProfile(TimestampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sales_rep_profile"
    )
    businesses_onboarded = models.ManyToManyField(
        Business, blank=True, related_name="onboarded_by_reps"
    )
    commission_rate = models.DecimalField(max_digits=4, decimal_places=3, default=Decimal("0.020"))

    class Meta:
        verbose_name = "Sales rep profile"

    def __str__(self) -> str:
        return f"Rep<{self.user.email}>"
