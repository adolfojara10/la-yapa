"""Order tests — UUID PK, pickup code, signals."""

import re
import uuid

import pytest

from .factories import OrderFactory
from .models import OrderStatus


@pytest.mark.django_db
def test_order_uses_uuid_pk():
    order = OrderFactory()
    assert isinstance(order.id, uuid.UUID)


@pytest.mark.django_db
def test_order_autogenerates_pickup_code_and_qr_token():
    order = OrderFactory()
    assert re.fullmatch(r"\d{4}", order.pickup_code)
    assert isinstance(order.pickup_qr_token, uuid.UUID)


@pytest.mark.django_db
def test_completing_order_updates_impact_stat():
    from apps.impact.models import ImpactStat

    order = OrderFactory(status=OrderStatus.PAID, quantity=2)
    consumer = order.consumer
    assert not ImpactStat.objects.filter(user=consumer).exists()

    order.status = OrderStatus.COMPLETED
    order.save()

    stat = ImpactStat.objects.get(user=consumer)
    assert stat.meals_rescued == 2
    assert stat.kg_food_saved > 0
    assert stat.co2_kg_saved > stat.kg_food_saved  # CO2 multiplier > 1
