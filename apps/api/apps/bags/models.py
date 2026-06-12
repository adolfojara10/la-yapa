"""Bags / listings + allergen tags."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.businesses.models import Business, BusinessLocation, BusinessStatus
from apps.core.models import TimestampedModel, UUIDPrimaryKeyModel
from apps.users.models import DietaryTag


class AllergenTag(TimestampedModel):
    """mani / gluten / lacteos / frutos_secos / mariscos / huevo / soya / etc."""

    name = models.CharField(max_length=40, unique=True)
    label_es = models.CharField(max_length=80)
    label_en = models.CharField(max_length=80, blank=True)
    icon_name = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Allergen tag"

    def __str__(self) -> str:
        return self.label_es or self.name


class BagType(models.TextChoices):
    SURPRISE = "surprise", "Surprise bag"
    SPECIFIC = "specific", "Specific items"


class BagQuerySet(models.QuerySet):
    def active(self):
        now = timezone.now()
        return self.filter(
            is_active=True,
            quantity_available__gt=0,
            pickup_window_end__gt=now,
            business_location__business__status=BusinessStatus.APPROVED,
        )


class Bag(UUIDPrimaryKeyModel, TimestampedModel):
    """A surprise bag or specific-items listing.

    Validation enforced in `clean()`:
        sale_price <= 0.5 * original_price  (≥50% discount)
        sale_price >= 1.50                  (floor to keep gross margin viable)
    """

    MIN_SALE_PRICE = Decimal("1.50")
    MAX_DISCOUNT_RATIO = Decimal("0.5")

    business_location = models.ForeignKey(
        BusinessLocation, on_delete=models.CASCADE, related_name="bags"
    )
    type = models.CharField(max_length=10, choices=BagType.choices, default=BagType.SURPRISE)
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    extra_image_urls = models.JSONField(default=list, blank=True, help_text="Used by specific bags")

    original_price = models.DecimalField(max_digits=8, decimal_places=2)
    sale_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity_available = models.PositiveIntegerField(default=0)
    quantity_total = models.PositiveIntegerField(default=0)

    dietary_tags = models.ManyToManyField(DietaryTag, blank=True, related_name="bags")
    allergen_warnings = models.ManyToManyField(AllergenTag, blank=True, related_name="bags")

    pickup_window_start = models.DateTimeField()
    pickup_window_end = models.DateTimeField()

    is_active = models.BooleanField(default=True, db_index=True)
    is_suspended_meal_eligible = models.BooleanField(default=False)

    objects = BagQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "pickup_window_end"]),
            models.Index(fields=["business_location", "is_active"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(pickup_window_end__gt=models.F("pickup_window_start")),
                name="bag_pickup_window_valid",
            ),
            models.CheckConstraint(
                check=models.Q(sale_price__gte=Decimal("0")),
                name="bag_sale_price_non_negative",
            ),
            models.CheckConstraint(
                check=models.Q(original_price__gt=Decimal("0")),
                name="bag_original_price_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} @ {self.business_location.business.name}"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}

        if self.original_price is not None and self.sale_price is not None:
            max_allowed = (self.original_price * self.MAX_DISCOUNT_RATIO).quantize(Decimal("0.01"))
            if self.sale_price > max_allowed:
                errors["sale_price"] = _(
                    "Sale price must be at most 50%% of original price (max %(max).2f)."
                ) % {"max": max_allowed}

            if self.sale_price < self.MIN_SALE_PRICE:
                errors["sale_price"] = _("Sale price must be at least %(min).2f.") % {
                    "min": self.MIN_SALE_PRICE
                }

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Initialize quantity_total snapshot the first time the bag is saved.
        if self._state.adding and not self.quantity_total:
            self.quantity_total = self.quantity_available
        self.full_clean()
        super().save(*args, **kwargs)

    # ----- Helpers -----
    @property
    def discount_percent(self) -> int:
        if not self.original_price or self.original_price == 0:
            return 0
        ratio = (self.original_price - self.sale_price) / self.original_price
        return int((ratio * 100).quantize(Decimal("1")))


class BagTemplate(UUIDPrimaryKeyModel, TimestampedModel):
    """Reusable bag presets owned by a business."""

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="bag_templates")
    name = models.CharField(max_length=140)
    type = models.CharField(max_length=10, choices=BagType.choices, default=BagType.SURPRISE)
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    original_price = models.DecimalField(max_digits=8, decimal_places=2)
    sale_price = models.DecimalField(max_digits=8, decimal_places=2)
    dietary_tags = models.ManyToManyField(DietaryTag, blank=True, related_name="bag_templates")
    allergen_warnings = models.ManyToManyField(
        AllergenTag,
        blank=True,
        related_name="bag_templates",
    )
    is_suspended_meal_eligible = models.BooleanField(default=False)

    class Meta:
        ordering = ["name", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "name"],
                name="uniq_bag_template_name_per_business",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} @ {self.business.name}"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}

        if self.original_price is not None and self.sale_price is not None:
            max_allowed = (Bag.MAX_DISCOUNT_RATIO * self.original_price).quantize(Decimal("0.01"))
            if self.sale_price > max_allowed:
                errors["sale_price"] = _(
                    "Sale price must be at most 50%% of original price (max %(max).2f)."
                ) % {"max": max_allowed}
            if self.sale_price < Bag.MIN_SALE_PRICE:
                errors["sale_price"] = _("Sale price must be at least %(min).2f.") % {
                    "min": Bag.MIN_SALE_PRICE
                }

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
