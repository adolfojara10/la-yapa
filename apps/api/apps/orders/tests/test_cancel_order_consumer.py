"""Consumer-side cancellation: window enforcement + refund routing."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.bags.factories import BagFactory
from apps.orders.factories import OrderFactory
from apps.orders.models import CancelledBy, OrderStatus
from apps.orders.services import (
    CancellationNotAllowed,
    CancellationOutsideWindow,
    cancel_order,
    create_order,
)
from apps.payments.models import PaymentStatus, PaymentTransaction


@pytest.mark.django_db
def test_consumer_cancel_before_window_refunds_inventory_and_status(consumer, fresh_bag):
    initial_qty = fresh_bag.quantity_available
    order = create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=2)
    result = cancel_order(order=order, actor=CancelledBy.CONSUMER, reason="changed my mind")

    fresh_bag.refresh_from_db()
    # Cancel restored what create_order debited → back to initial.
    assert fresh_bag.quantity_available == initial_qty
    assert result.order.status == OrderStatus.CANCELLED
    assert result.triggered_refund is False
    assert result.granted_bonus_credit_id is None


@pytest.mark.django_db(transaction=True)
def test_consumer_cancel_of_paid_order_routes_to_pending_refund(consumer, fresh_bag):
    # `transaction=True` lets `transaction.on_commit` actually fire inside the
    # test (default django_db wraps each test in a savepoint that never commits).
    order = create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=1)
    # Simulate the webhook having marked it paid + persisted a SUCCESS tx.
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])
    PaymentTransaction.objects.create(
        order=order,
        provider="fake",
        provider_transaction_id="fake-tx-1",
        amount=order.total_paid,
        status=PaymentStatus.SUCCESS,
    )
    result = cancel_order(order=order, actor=CancelledBy.CONSUMER)
    assert result.triggered_refund is True
    order.refresh_from_db()
    # FakePaymentProvider is synchronous + always succeeds → final state is REFUNDED.
    assert order.status == OrderStatus.REFUNDED


@pytest.mark.django_db
def test_consumer_cannot_cancel_after_window(consumer):
    """Within 1h of pickup_window_start → cancellation denied."""
    bag = BagFactory(
        pickup_window_start=timezone.now() + timedelta(minutes=30),
        pickup_window_end=timezone.now() + timedelta(hours=2),
        quantity_available=3,
    )
    order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    with pytest.raises(CancellationOutsideWindow):
        cancel_order(order=order, actor=CancelledBy.CONSUMER)


@pytest.mark.django_db
def test_consumer_can_cancel_exactly_at_1h_boundary(consumer):
    """Exactly 1h before pickup → still inside window (boundary inclusive)."""
    bag = BagFactory(
        pickup_window_start=timezone.now() + timedelta(hours=1, seconds=1),
        pickup_window_end=timezone.now() + timedelta(hours=3),
        quantity_available=3,
    )
    order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    result = cancel_order(order=order, actor=CancelledBy.CONSUMER)
    assert result.order.status == OrderStatus.CANCELLED


@pytest.mark.django_db
def test_cannot_cancel_terminal_order(consumer, fresh_bag):
    order = OrderFactory(
        consumer=consumer,
        bag=fresh_bag,
        business_location=fresh_bag.business_location,
        status=OrderStatus.COMPLETED,
        original_price_snapshot=Decimal("10"),
        sale_price_snapshot=Decimal("3"),
        total_paid=Decimal("3"),
    )
    with pytest.raises(CancellationNotAllowed):
        cancel_order(order=order, actor=CancelledBy.CONSUMER)


@pytest.mark.django_db
def test_cancel_persists_actor_reason_and_timestamp(consumer, fresh_bag):
    order = create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=1)
    cancel_order(order=order, actor=CancelledBy.CONSUMER, reason="too far")
    order.refresh_from_db()
    assert order.cancelled_by == CancelledBy.CONSUMER
    assert order.cancellation_reason == "too far"
    assert order.cancelled_at is not None
