"""Business-side cancellation: bonus credit + payout line item."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.orders.models import CancelledBy, OrderStatus
from apps.orders.services import cancel_order, create_order
from apps.payments.models import (
    BonusCredit,
    BonusCreditSource,
    PaymentStatus,
    PaymentTransaction,
    PayoutLineItem,
    PayoutLineItemType,
)


@pytest.mark.django_db
def test_business_cancel_grants_one_dollar_bonus_credit(consumer, fresh_bag):
    order = create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=1)
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])
    PaymentTransaction.objects.create(
        order=order,
        provider="fake",
        provider_transaction_id="fake-tx-2",
        amount=order.total_paid,
        status=PaymentStatus.SUCCESS,
    )

    result = cancel_order(order=order, actor=CancelledBy.BUSINESS, reason="sold_out")

    assert result.granted_bonus_credit_id is not None
    credit = BonusCredit.objects.get(pk=result.granted_bonus_credit_id)
    assert credit.user == consumer
    assert credit.amount == Decimal("1.00")
    assert credit.source == BonusCreditSource.BUSINESS_CANCELLATION
    assert credit.source_business == fresh_bag.business_location.business
    assert credit.source_order == order


@pytest.mark.django_db
def test_business_cancel_writes_payout_line_item_deduction(consumer, fresh_bag):
    order = create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=1)
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])
    PaymentTransaction.objects.create(
        order=order,
        provider="fake",
        provider_transaction_id="fake-tx-3",
        amount=order.total_paid,
        status=PaymentStatus.SUCCESS,
    )

    cancel_order(order=order, actor=CancelledBy.BUSINESS)

    line_items = PayoutLineItem.objects.filter(
        order=order, type=PayoutLineItemType.BONUS_CREDIT_DEDUCTION
    )
    assert line_items.count() == 1
    assert line_items.first().amount == Decimal("-1.00")
    assert line_items.first().payout.business == fresh_bag.business_location.business


@pytest.mark.django_db
def test_consumer_cancel_does_not_grant_bonus_credit(consumer, fresh_bag):
    order = create_order(consumer=consumer, bag_id=fresh_bag.id, quantity=1)
    result = cancel_order(order=order, actor=CancelledBy.CONSUMER)
    assert result.granted_bonus_credit_id is None
    assert not BonusCredit.objects.filter(user=consumer).exists()
