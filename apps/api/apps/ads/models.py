"""AdCampaign (Phase 3 — stub)."""

from __future__ import annotations

from decimal import Decimal

from django.db import models

from apps.businesses.models import Business
from apps.core.models import TimestampedModel


class AdCampaignType(models.TextChoices):
    FEATURED_LISTING = "featured_listing", "Featured listing"
    BANNER = "banner", "Banner"
    SPONSORED_SEARCH = "sponsored_search", "Sponsored search"


class AdCampaignStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    ENDED = "ended", "Ended"


class AdCampaign(TimestampedModel):
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="ad_campaigns")
    type = models.CharField(max_length=20, choices=AdCampaignType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    status = models.CharField(
        max_length=12, choices=AdCampaignStatus.choices, default=AdCampaignStatus.DRAFT
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Ad<{self.business.name} · {self.type}>"
