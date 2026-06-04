"""Payment service: process_payment + refund_payment (fake provider)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.orders.models import OrderStatus
from apps.orders.services import cancel_order, create_order
from apps.payments.models import PaymentStatus, PaymentTransaction
from apps.payments.services import PaymentError, process_payment, refund_payment


@pytest.mark.django_db
def test_process_payment_creates_session_and_pending_tx(pending_order):
    ctx = process_payment(
        order=pending_order,
        provider_name="payphone",
        return_url="layapa://payment-result",
    )
    assert ctx.session.webview_url.startswith("https://fake.layapa.test/")
    tx = PaymentTransaction.objects.get(order=pending_order)
    assert tx.status == PaymentStatus.PENDING
    assert tx.amount == pending_order.total_paid
    assert tx.provider == "payphone"


@pytest.mark.django_db
def test_process_payment_rejects_non_pending_order(pending_order):
    pending_order.status = OrderStatus.PAID
    pending_order.save(update_fields=["status"])
    with pytest.raises(PaymentError) as exc:
        process_payment(
            order=pending_order,
            provider_name="payphone",
            return_url="layapa://payment-result",
        )
    assert exc.value.code == "invalid_status"


@pytest.mark.django_db
def test_refund_payment_with_success_tx_flips_to_refunded(consumer):
    from datetime import timedelta

    from django.utils import timezone

    from apps.bags.factories import BagFactory

    bag = BagFactory(
        original_price=Decimal("12.00"),
        sale_price=Decimal("4.50"),
        quantity_available=3,
        pickup_window_start=timezone.now() + timedelta(hours=4),
        pickup_window_end=timezone.now() + timedelta(hours=6),
    )
    order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])
    PaymentTransaction.objects.create(
        order=order,
        provider="payphone",
        provider_transaction_id="fake-tx-refund",
        amount=order.total_paid,
        status=PaymentStatus.SUCCESS,
    )
    # Move to pending_refund (matches the cancel_order flow precondition).
    order.status = OrderStatus.PENDING_REFUND
    order.save(update_fields=["status"])

    refund_payment(order, reason="user cancelled")

    order.refresh_from_db()
    assert order.status == OrderStatus.REFUNDED
    tx = PaymentTransaction.objects.get(order=order)
    assert tx.status == PaymentStatus.REFUNDED
    assert tx.refund_provider_transaction_id.startswith("fake-rfd-")


@pytest.mark.django_db
def test_refund_payment_without_success_tx_short_circuits_to_cancelled(consumer):
    """If the order is in PENDING_REFUND but there's no SUCCESS tx (edge
    case: data corruption / out-of-band ops mutation), we don't hit the
    provider; the order falls back to CANCELLED."""
    from datetime import timedelta

    from django.utils import timezone

    from apps.bags.factories import BagFactory

    bag = BagFactory(
        pickup_window_start=timezone.now() + timedelta(hours=4),
        pickup_window_end=timezone.now() + timedelta(hours=6),
        quantity_available=3,
    )
    order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    order.status = OrderStatus.PENDING_REFUND
    order.save(update_fields=["status"])

    refund_payment(order, reason="ops cleanup")

    order.refresh_from_db()
    assert order.status == OrderStatus.CANCELLED


@pytest.mark.django_db(transaction=True)
def test_cancel_order_then_refund_full_happy_path(consumer):
    from datetime import timedelta

    from django.utils import timezone

    from apps.bags.factories import BagFactory
    from apps.orders.models import CancelledBy

    bag = BagFactory(
        original_price=Decimal("12"),
        sale_price=Decimal("4.50"),
        quantity_available=3,
        pickup_window_start=timezone.now() + timedelta(hours=4),
        pickup_window_end=timezone.now() + timedelta(hours=6),
    )
    order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])
    PaymentTransaction.objects.create(
        order=order,
        provider="payphone",
        provider_transaction_id="fake-tx-cancel-flow",
        amount=order.total_paid,
        status=PaymentStatus.SUCCESS,
    )

    result = cancel_order(order=order, actor=CancelledBy.CONSUMER)
    assert result.triggered_refund is True
    order.refresh_from_db()  # on_commit hook ran the refund after cancel returned
    assert order.status == OrderStatus.REFUNDED  # fake provider is sync+ok
