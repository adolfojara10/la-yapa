"""Per-user cached impact stats — refreshed by signals on order completion."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import TimestampedModel


class ImpactStat(TimestampedModel):
    """Denormalized cache. Source of truth = completed Orders; this is for fast reads."""

    # CO2-saved heuristic: each kg of rescued food avoids ~2.5 kg CO2-equivalent.
    # See https://ourworldindata.org/food-waste-emissions for the methodology bracket.
    CO2_PER_KG_FOOD = Decimal("2.5")
    # Conservative estimate: 1 surprise bag ≈ 0.6 kg of food.
    KG_PER_MEAL = Decimal("0.6")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="impact_stat"
    )
    meals_rescued = models.PositiveIntegerField(default=0)
    kg_food_saved = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    co2_kg_saved = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    money_saved = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    last_calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Impact stat"

    def __str__(self) -> str:
        return f"Impact<{self.user.email}: {self.meals_rescued} meals>"
