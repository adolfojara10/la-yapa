"""BonusCredit model + apply_bonus_credit service."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.orders.models import OrderStatus
from apps.payments.models import BonusCredit, BonusCreditSource
from apps.payments.services import CreditError, apply_bonus_credit


def _credit(user, amount="1.00", expires_in_days: int | None = 90, redeemed=False):
    expires_at = timezone.now() + timedelta(days=expires_in_days) if expires_in_days else None
    return BonusCredit.objects.create(
        user=user,
        amount=Decimal(amount),
        source=BonusCreditSource.PROMO,
        expires_at=expires_at,
        redeemed_at=timezone.now() if redeemed else None,
    )


@pytest.mark.django_db
def test_available_balance_sums_active_credits(consumer):
    _credit(consumer, "1.00")
    _credit(consumer, "2.50")
    _credit(consumer, "5.00", redeemed=True)  # not counted
    _credit(consumer, "1.00", expires_in_days=-1)  # expired, not counted
    assert BonusCredit.available_balance_for(consumer) == Decimal("3.50")


@pytest.mark.django_db
def test_apply_credit_reduces_total_paid(pending_order, consumer):
    credit = _credit(consumer, "2.00")
    original_total = pending_order.total_paid
    applied = apply_bonus_credit(order=pending_order, credit_id=credit.id)

    assert applied == Decimal("2.00")
    pending_order.refresh_from_db()
    assert pending_order.applied_credit_amount == Decimal("2.00")
    assert pending_order.total_paid == original_total - Decimal("2.00")

    credit.refresh_from_db()
    assert credit.redeemed_in_order_id == pending_order.id
    assert credit.redeemed_at is not None


@pytest.mark.django_db
def test_apply_credit_clamps_to_order_total(pending_order, consumer):
    """A $50 credit on a $4.50 order applies only $4.50."""
    credit = _credit(consumer, "50.00")
    applied = apply_bonus_credit(order=pending_order, credit_id=credit.id)
    assert applied == Decimal("4.50")
    pending_order.refresh_from_db()
    assert pending_order.total_paid == Decimal("0.00")


@pytest.mark.django_db
def test_apply_credit_rejects_other_users_credit(pending_order, consumer_b):
    credit = _credit(consumer_b, "1.00")
    with pytest.raises(CreditError) as exc:
        apply_bonus_credit(order=pending_order, credit_id=credit.id)
    assert exc.value.code == "credit_wrong_user"


@pytest.mark.django_db
def test_apply_credit_rejects_already_redeemed(pending_order, consumer):
    credit = _credit(consumer, "1.00", redeemed=True)
    with pytest.raises(CreditError) as exc:
        apply_bonus_credit(order=pending_order, credit_id=credit.id)
    assert exc.value.code == "credit_already_redeemed"


@pytest.mark.django_db
def test_apply_credit_rejects_expired(pending_order, consumer):
    credit = _credit(consumer, "1.00", expires_in_days=-1)
    with pytest.raises(CreditError) as exc:
        apply_bonus_credit(order=pending_order, credit_id=credit.id)
    assert exc.value.code == "credit_expired"


@pytest.mark.django_db
def test_apply_credit_rejects_order_not_pending_payment(pending_order, consumer):
    pending_order.status = OrderStatus.PAID
    pending_order.save(update_fields=["status"])
    credit = _credit(consumer, "1.00")
    with pytest.raises(CreditError) as exc:
        apply_bonus_credit(order=pending_order, credit_id=credit.id)
    assert exc.value.code == "invalid_status"
