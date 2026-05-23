"""PaymentTransaction · Payout · PayoutLineItem · Invoice."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.businesses.models import Business
from apps.core.models import TimestampedModel
from apps.orders.models import Order


class PaymentProvider(models.TextChoices):
    PAYPHONE = "payphone", "PayPhone"
    DE_UNA = "de_una", "DeUna"
    KUSHKI = "kushki", "Kushki"
    STRIPE = "stripe", "Stripe"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class PaymentTransaction(TimestampedModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="transactions")
    provider = models.CharField(max_length=20, choices=PaymentProvider.choices)
    provider_transaction_id = models.CharField(max_length=128, blank=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, db_index=True
    )
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Tx<{self.provider}:{self.provider_transaction_id or self.pk}>"


class PayoutStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    PROCESSING = "processing", "Processing"
    PAID = "paid", "Paid"
    FAILED = "failed", "Failed"


class Payout(TimestampedModel):
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="payouts")
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    total_orders = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=12, choices=PayoutStatus.choices, default=PayoutStatus.PENDING, db_index=True
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payouts_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    bank_reference = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(period_end__gt=models.F("period_start")),
                name="payout_period_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"Payout<{self.business.name} · {self.period_start:%Y-%m-%d}>"


class PayoutLineItemType(models.TextChoices):
    SALE = "sale", "Sale"
    REFUND_DEDUCTION = "refund_deduction", "Refund deduction"
    BONUS_CREDIT_DEDUCTION = "bonus_credit_deduction", "Bonus credit deduction"


class PayoutLineItem(TimestampedModel):
    payout = models.ForeignKey(Payout, on_delete=models.CASCADE, related_name="line_items")
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payout_line_items")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=30, choices=PayoutLineItemType.choices)

    class Meta:
        ordering = ["payout", "id"]

    def __str__(self) -> str:
        return f"Line<{self.type}:{self.amount}>"


class InvoiceType(models.TextChoices):
    CONSUMER_INVOICE = "consumer_invoice", "Consumer invoice"
    PLATFORM_COMMISSION_INVOICE = "platform_commission_invoice", "Platform commission invoice"


class InvoiceStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    AUTHORIZED = "authorized", "Authorized"
    REJECTED = "rejected", "Rejected"


class Invoice(TimestampedModel):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="invoices")
    type = models.CharField(max_length=40, choices=InvoiceType.choices)
    sri_authorization_number = models.CharField(max_length=64, blank=True, db_index=True)
    sri_xml_url = models.URLField(blank=True)
    pdf_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=12, choices=InvoiceStatus.choices, default=InvoiceStatus.PENDING, db_index=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Invoice<{self.type}:{self.order_id}>"
