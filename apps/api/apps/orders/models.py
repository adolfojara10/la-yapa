"""Order + Dispute. Both use UUID PKs (security: pickup codes / dispute IDs travel in URLs)."""

from __future__ import annotations

import secrets
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.bags.models import Bag
from apps.businesses.models import BusinessLocation
from apps.core.models import TimestampedModel, UUIDPrimaryKeyModel


def _generate_pickup_code() -> str:
    """4-digit numeric pickup code. Not unique globally — only needs to be unique per business per day."""
    return f"{secrets.randbelow(10_000):04d}"


class OrderStatus(models.TextChoices):
    PENDING_PAYMENT = "pending_payment", "Pending payment"
    PAID = "paid", "Paid"
    READY_FOR_PICKUP = "ready_for_pickup", "Ready for pickup"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"
    EXPIRED = "expired", "Expired"


class CancelledBy(models.TextChoices):
    CONSUMER = "consumer", "Consumer"
    BUSINESS = "business", "Business"
    ADMIN = "admin", "Admin"
    SYSTEM = "system", "System"


class PaymentMethod(models.TextChoices):
    PAYPHONE = "payphone", "PayPhone"
    DE_UNA = "de_una", "DeUna"
    KUSHKI = "kushki", "Kushki"
    STRIPE = "stripe", "Stripe"
    CASH = "cash", "Cash"


class Order(UUIDPrimaryKeyModel, TimestampedModel):
    consumer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    bag = models.ForeignKey(Bag, on_delete=models.PROTECT, related_name="orders")
    # Snapshot of where the bag was at purchase time — survives a later relocation.
    business_location = models.ForeignKey(
        BusinessLocation, on_delete=models.PROTECT, related_name="orders"
    )

    quantity = models.PositiveSmallIntegerField(default=1)
    original_price_snapshot = models.DecimalField(max_digits=8, decimal_places=2)
    sale_price_snapshot = models.DecimalField(max_digits=8, decimal_places=2)
    total_paid = models.DecimalField(max_digits=8, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    business_payout_amount = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0")
    )

    pickup_code = models.CharField(max_length=4, default=_generate_pickup_code)
    pickup_qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING_PAYMENT,
        db_index=True,
    )
    cancelled_by = models.CharField(max_length=10, choices=CancelledBy.choices, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)

    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, blank=True)
    payment_provider_ref = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["consumer", "status"]),
            models.Index(fields=["business_location", "status"]),
            models.Index(fields=["pickup_code"]),
        ]

    def __str__(self) -> str:
        return f"Order<{self.id} · {self.status}>"


class DisputeOpenedBy(models.TextChoices):
    CONSUMER = "consumer", "Consumer"
    BUSINESS = "business", "Business"


class DisputeStatus(models.TextChoices):
    OPEN = "open", "Open"
    UNDER_REVIEW = "under_review", "Under review"
    RESOLVED_REFUND = "resolved_refund", "Resolved — refund"
    RESOLVED_NO_REFUND = "resolved_no_refund", "Resolved — no refund"
    CLOSED = "closed", "Closed"


class Dispute(UUIDPrimaryKeyModel, TimestampedModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="disputes")
    opened_by = models.CharField(max_length=10, choices=DisputeOpenedBy.choices)
    reason = models.CharField(max_length=120)
    description = models.TextField()
    evidence_urls = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20, choices=DisputeStatus.choices, default=DisputeStatus.OPEN, db_index=True
    )
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="disputes_resolved",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Dispute<{self.id} · {self.status}>"
