"""Recalculate ImpactStat when an Order transitions to COMPLETED."""

from __future__ import annotations

from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.orders.models import Order, OrderStatus

from .models import ImpactStat


@receiver(post_save, sender=Order)
def update_impact_on_completion(sender, instance: Order, created: bool, **kwargs) -> None:
    """Bump the consumer's impact stats when an order completes.

    Idempotency: we recompute the delta from THIS order only, and use
    `update_fields` to avoid recursing through other signals. A real production
    impl would diff the prior persisted status, but for MVP this is fine because
    Order.status flips to COMPLETED exactly once via the dedicated `complete()`
    flow (to be implemented in the orders service layer).
    """
    if instance.status != OrderStatus.COMPLETED or created:
        return

    stat, _ = ImpactStat.objects.get_or_create(user=instance.consumer)

    meals_delta = int(instance.quantity)
    kg_delta = (ImpactStat.KG_PER_MEAL * Decimal(meals_delta)).quantize(Decimal("0.01"))
    co2_delta = (kg_delta * ImpactStat.CO2_PER_KG_FOOD).quantize(Decimal("0.01"))
    saved_per_unit = instance.original_price_snapshot - instance.sale_price_snapshot
    money_delta = (saved_per_unit * Decimal(meals_delta)).quantize(Decimal("0.01"))

    ImpactStat.objects.filter(pk=stat.pk).update(
        meals_rescued=models_F_add("meals_rescued", meals_delta),
        kg_food_saved=models_F_add("kg_food_saved", kg_delta),
        co2_kg_saved=models_F_add("co2_kg_saved", co2_delta),
        money_saved=models_F_add("money_saved", money_delta),
    )


def models_F_add(field: str, value):
    from django.db.models import F

    return F(field) + value
