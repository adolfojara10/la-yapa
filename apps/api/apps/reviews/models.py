"""Review (one per Order)."""

from __future__ import annotations

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.businesses.models import BusinessLocation
from apps.core.models import TimestampedModel
from apps.orders.models import Order


class Review(TimestampedModel):
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="review")
    consumer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reviews_written"
    )
    business_location = models.ForeignKey(
        BusinessLocation, on_delete=models.PROTECT, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.CharField(max_length=500, blank=True)
    is_visible = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["business_location", "is_visible"])]

    def __str__(self) -> str:
        return f"Review<{self.rating}★ by {self.consumer.email}>"
