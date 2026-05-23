"""Suspended meals — pay-it-forward donations to be claimed by businesses for redistribution."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.bags.models import Bag
from apps.businesses.models import BusinessLocation
from apps.core.models import TimestampedModel, UUIDPrimaryKeyModel


class DonationStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CLAIMED = "claimed", "Claimed"
    EXPIRED = "expired", "Expired"


class SuspendedMealDonation(UUIDPrimaryKeyModel, TimestampedModel):
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="donations"
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    bag = models.ForeignKey(
        Bag,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="suspended_donations",
        help_text="Specific bag, or null for the general pool.",
    )
    status = models.CharField(
        max_length=10, choices=DonationStatus.choices, default=DonationStatus.ACTIVE, db_index=True
    )
    claimed_by_business = models.ForeignKey(
        BusinessLocation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="claimed_donations",
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    is_anonymous = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Donation<{self.amount} · {self.status}>"


class SuspendedMealClaim(TimestampedModel):
    donation = models.ForeignKey(
        SuspendedMealDonation, on_delete=models.PROTECT, related_name="claims"
    )
    business_location = models.ForeignKey(
        BusinessLocation, on_delete=models.PROTECT, related_name="suspended_claims"
    )
    beneficiary_notes = models.TextField(blank=True)
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-claimed_at"]

    def __str__(self) -> str:
        return f"Claim<{self.donation_id} · {self.business_location}>"
