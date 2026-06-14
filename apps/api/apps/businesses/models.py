"""Businesses domain: Business + BusinessLocation + BusinessVerification + Favorite."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from encrypted_model_fields.fields import EncryptedCharField

from apps.core.models import TimestampedModel
from apps.geo.fields import PointField


class BusinessType(models.TextChoices):
    RESTAURANT = "restaurant", "Restaurant"
    BAKERY = "bakery", "Bakery"
    SUPERMARKET = "supermarket", "Supermarket"
    HOTEL = "hotel", "Hotel"
    MERCADO = "mercado", "Mercado"
    FARMER = "farmer", "Farmer"
    OTHER = "other", "Other"


class BusinessTier(models.TextChoices):
    FORMAL = "formal", "Formal (RUC required)"
    INFORMAL = "informal", "Informal (mercado/farmer)"


class BusinessStatus(models.TextChoices):
    PENDING = "pending", "Pending review"
    APPROVED = "approved", "Approved"
    SUSPENDED = "suspended", "Suspended"
    REJECTED = "rejected", "Rejected"


class PayoutFrequency(models.TextChoices):
    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"


class PayoutMethod(models.TextChoices):
    BANK_TRANSFER = "bank_transfer", "Bank transfer"
    DE_UNA = "de_una", "DeUna"


class BusinessManager(models.Manager):
    def approved(self):
        return self.filter(status=BusinessStatus.APPROVED)


class Business(TimestampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="businesses"
    )
    name = models.CharField(max_length=140)
    business_type = models.CharField(max_length=20, choices=BusinessType.choices)
    tier = models.CharField(
        max_length=10, choices=BusinessTier.choices, default=BusinessTier.FORMAL
    )
    description = models.TextField(blank=True)
    logo_url = models.URLField(blank=True)
    cover_url = models.URLField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    status = models.CharField(
        max_length=20, choices=BusinessStatus.choices, default=BusinessStatus.PENDING, db_index=True
    )
    rejection_reason = models.TextField(blank=True)
    review_notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="businesses_approved",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    payout_frequency = models.CharField(
        max_length=10, choices=PayoutFrequency.choices, default=PayoutFrequency.WEEKLY
    )
    payout_method = models.CharField(
        max_length=20, choices=PayoutMethod.choices, default=PayoutMethod.BANK_TRANSFER
    )
    # Encrypted JSON-as-text. Holds {bank_name, account_number, account_type, holder, …}.
    bank_account = EncryptedCharField(max_length=512, blank=True, default="")

    commission_rate = models.DecimalField(max_digits=4, decimal_places=3, default=Decimal("0.180"))

    objects = BusinessManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Businesses"
        indexes = [models.Index(fields=["business_type", "status"])]

    def __str__(self) -> str:
        return self.name

    @property
    def is_food_business(self) -> bool:
        return self.business_type in {
            BusinessType.RESTAURANT,
            BusinessType.BAKERY,
            BusinessType.SUPERMARKET,
            BusinessType.HOTEL,
            BusinessType.MERCADO,
            BusinessType.FARMER,
        }

    @property
    def has_locations(self) -> bool:
        return self.locations.filter(is_active=True).exists()


class BusinessLocation(TimestampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=140, help_text='e.g. "Sucursal Centro"')
    address = models.CharField(max_length=255)
    location = PointField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    hours_of_operation = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["business__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "name"], name="uniq_business_location_name"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.business.name} — {self.name}"


class BusinessVerification(TimestampedModel):
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name="verification")
    ruc_number = models.CharField(max_length=20, blank=True)
    ruc_document_url = models.URLField(blank=True)
    cedula_number = models.CharField(max_length=20, blank=True)
    cedula_document_url = models.URLField(blank=True)
    selfie_with_cedula_url = models.URLField(blank=True)
    permiso_funcionamiento_url = models.URLField(blank=True)
    arcsa_url = models.URLField(blank=True)
    bank_proof_url = models.URLField(blank=True)
    business_photo_url = models.URLField(blank=True)
    food_safety_terms_accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Business verification"
        verbose_name_plural = "Business verifications"

    def __str__(self) -> str:
        return f"Verification<{self.business.name}>"


class Favorite(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    business_location = models.ForeignKey(
        BusinessLocation, on_delete=models.CASCADE, related_name="favorited_by"
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "business_location"], name="uniq_favorite_per_user_location"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} ♥ {self.business_location}"
