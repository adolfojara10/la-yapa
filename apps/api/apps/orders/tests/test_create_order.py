"""Order creation service: inventory lock, pricing, suspended-meal flag."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.bags.factories import BagFactory
from apps.orders.models import Order, OrderStatus
from apps.orders.services import (
    BagUnavailable,
    InsufficientStock,
    OrderServiceError,
    create_order,
)


@pytest.mark.django_db
def test_create_order_happy_path(consumer, fresh_bag):
    initial_qty = fresh_bag.quantity_available
    order = create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=2)

    assert order.status == OrderStatus.PENDING_PAYMENT
    assert order.quantity == 2
    assert order.total_paid == Decimal("9.00")  # 4.50 * 2

    fresh_bag.refresh_from_db()
    assert fresh_bag.quantity_available == initial_qty - 2


@pytest.mark.django_db
def test_create_order_records_price_snapshots(consumer, fresh_bag):
    order = create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=1)
    assert order.original_price_snapshot == fresh_bag.original_price
    assert order.sale_price_snapshot == fresh_bag.sale_price


@pytest.mark.django_db
def test_create_order_computes_commission_and_payout(consumer, fresh_bag):
    order = create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=2)
    # default commission_rate is 0.180 → 18% of 9.00 = 1.62
    assert order.platform_commission == Decimal("1.62")
    assert order.business_payout_amount == Decimal("7.38")


@pytest.mark.django_db
def test_create_order_carries_suspended_meal_flag(consumer, fresh_bag):
    order = create_order(
        consumer=consumer,
        bag_id=fresh_bag.id,
        quantity=1,
        donate_as_suspended_meal=True,
    )
    assert order.donate_as_suspended_meal is True


@pytest.mark.django_db
def test_create_order_rejects_zero_quantity(consumer, fresh_bag):
    with pytest.raises(OrderServiceError) as exc:
        create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=0)
    assert exc.value.code == "invalid_quantity"


@pytest.mark.django_db
def test_create_order_rejects_missing_bag(consumer):
    import uuid

    with pytest.raises(BagUnavailable):
        create_order(consumer=consumer, bag_id=uuid.uuid4(), quantity=1)


@pytest.mark.django_db
def test_create_order_rejects_inactive_bag(consumer):
    bag = BagFactory(
        is_active=False,
        pickup_window_start=timezone.now() + timedelta(hours=4),
        pickup_window_end=timezone.now() + timedelta(hours=6),
    )
    with pytest.raises(BagUnavailable):
        create_order(consumer=consumer, bag_id=bag.id, quantity=1)


@pytest.mark.django_db
def test_create_order_rejects_expired_window(consumer):
    bag = BagFactory(
        pickup_window_start=timezone.now() - timedelta(hours=2),
        pickup_window_end=timezone.now() - timedelta(hours=1),
    )
    # Bag is .active() filtered but we may receive an expired bag via direct PK.
    with pytest.raises(BagUnavailable):
        create_order(consumer=consumer, bag_id=bag.id, quantity=1)


@pytest.mark.django_db
def test_create_order_rejects_oversell(consumer, low_stock_bag):
    with pytest.raises(InsufficientStock):
        create_order(consumer=consumer, bag_id=low_stock_bag.id, quantity=2)


@pytest.mark.django_db
def test_create_order_inventory_restored_on_exception(consumer, fresh_bag, monkeypatch):
    """If anything blows up inside the transaction, inventory must NOT be debited."""
    from apps.orders import services

    initial_qty = fresh_bag.quantity_available

    def boom(*args, **kwargs):
        raise RuntimeError("explode after debit")

    monkeypatch.setattr(services.Order.objects, "create", boom)
    with pytest.raises(RuntimeError):
        create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=1)

    fresh_bag.refresh_from_db()
    assert fresh_bag.quantity_available == initial_qty
    assert not Order.objects.filter(bag=fresh_bag, consumer=consumer).exists()
