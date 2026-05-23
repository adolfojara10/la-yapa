"""Bag pricing + lifecycle tests."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from .factories import BagFactory
from .models import Bag


@pytest.mark.django_db
def test_bag_factory_persists():
    bag = BagFactory()
    assert bag.pk is not None
    assert bag.quantity_total == bag.quantity_available  # snapshot taken on first save


@pytest.mark.django_db
def test_bag_rejects_sale_price_above_50_percent_discount():
    with pytest.raises(ValidationError) as exc:
        BagFactory(original_price=Decimal("10.00"), sale_price=Decimal("6.00"))
    assert "sale_price" in exc.value.message_dict


@pytest.mark.django_db
def test_bag_rejects_sale_price_below_floor():
    with pytest.raises(ValidationError) as exc:
        BagFactory(original_price=Decimal("10.00"), sale_price=Decimal("1.00"))
    assert "sale_price" in exc.value.message_dict


@pytest.mark.django_db
def test_bag_accepts_exactly_50_percent_discount():
    bag = BagFactory(original_price=Decimal("10.00"), sale_price=Decimal("5.00"))
    assert bag.pk is not None


@pytest.mark.django_db
def test_bag_discount_percent_computed_correctly():
    bag = BagFactory(original_price=Decimal("12.00"), sale_price=Decimal("3.60"))
    assert bag.discount_percent == 70


@pytest.mark.django_db
def test_bag_active_manager_excludes_expired():
    from datetime import timedelta

    from django.utils import timezone

    BagFactory()  # active
    BagFactory(
        pickup_window_start=timezone.now() - timedelta(hours=4),
        pickup_window_end=timezone.now() - timedelta(hours=1),
    )
    assert Bag.objects.active().count() == 1
