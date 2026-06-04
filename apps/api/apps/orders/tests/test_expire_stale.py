"""expire_stale_pending: cron-style sweep of abandoned pending_payment orders."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.orders.factories import OrderFactory
from apps.orders.models import OrderStatus
from apps.orders.services import expire_stale_pending


@pytest.mark.django_db
def test_expire_stale_marks_old_pending_orders_expired(fresh_bag):
    order = OrderFactory(
        bag=fresh_bag,
        business_location=fresh_bag.business_location,
        status=OrderStatus.PENDING_PAYMENT,
        original_price_snapshot=Decimal("10"),
        sale_price_snapshot=Decimal("3"),
        total_paid=Decimal("3"),
        quantity=1,
    )
    # Age it past the cutoff.
    aged = timezone.now() - timedelta(minutes=20)
    type(order).objects.filter(pk=order.pk).update(created_at=aged)

    count = expire_stale_pending(older_than_minutes=15)
    assert count == 1

    order.refresh_from_db()
    assert order.status == OrderStatus.EXPIRED


@pytest.mark.django_db
def test_expire_stale_skips_recent_pending(fresh_bag):
    order = OrderFactory(
        bag=fresh_bag,
        business_location=fresh_bag.business_location,
        status=OrderStatus.PENDING_PAYMENT,
        original_price_snapshot=Decimal("10"),
        sale_price_snapshot=Decimal("3"),
        total_paid=Decimal("3"),
        quantity=1,
    )
    count = expire_stale_pending(older_than_minutes=15)
    assert count == 0
    order.refresh_from_db()
    assert order.status == OrderStatus.PENDING_PAYMENT


@pytest.mark.django_db
def test_expire_stale_restores_inventory(fresh_bag):
    fresh_bag.quantity_available = 3
    fresh_bag.save(update_fields=["quantity_available"])
    order = OrderFactory(
        bag=fresh_bag,
        business_location=fresh_bag.business_location,
        status=OrderStatus.PENDING_PAYMENT,
        original_price_snapshot=Decimal("12"),
        sale_price_snapshot=Decimal("4.50"),
        total_paid=Decimal("9.00"),
        quantity=2,
    )
    aged = timezone.now() - timedelta(minutes=20)
    type(order).objects.filter(pk=order.pk).update(created_at=aged)

    expire_stale_pending(older_than_minutes=15)
    fresh_bag.refresh_from_db()
    assert fresh_bag.quantity_available == 5


@pytest.mark.django_db
def test_expire_stale_only_touches_pending_payment(fresh_bag):
    paid = OrderFactory(
        bag=fresh_bag,
        business_location=fresh_bag.business_location,
        status=OrderStatus.PAID,
        original_price_snapshot=Decimal("10"),
        sale_price_snapshot=Decimal("3"),
        total_paid=Decimal("3"),
    )
    type(paid).objects.filter(pk=paid.pk).update(created_at=timezone.now() - timedelta(hours=2))
    count = expire_stale_pending(older_than_minutes=15)
    assert count == 0
