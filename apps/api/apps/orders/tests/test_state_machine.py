"""State machine: allowed transitions, terminal status guards."""

from __future__ import annotations

import pytest

from apps.orders.models import OrderStatus
from apps.orders.state_machine import (
    ALLOWED_TRANSITIONS,
    InvalidTransition,
    assert_can_transition,
)


def test_pending_payment_can_pay_cancel_expire():
    allowed = ALLOWED_TRANSITIONS[OrderStatus.PENDING_PAYMENT]
    assert OrderStatus.PAID in allowed
    assert OrderStatus.CANCELLED in allowed
    assert OrderStatus.EXPIRED in allowed


def test_paid_can_transition_to_pending_refund_or_complete():
    allowed = ALLOWED_TRANSITIONS[OrderStatus.PAID]
    assert OrderStatus.PENDING_REFUND in allowed
    assert OrderStatus.COMPLETED in allowed


def test_terminal_statuses_have_no_outgoing_transitions():
    for terminal in (
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
        OrderStatus.REFUNDED,
        OrderStatus.EXPIRED,
    ):
        assert ALLOWED_TRANSITIONS[terminal] == frozenset()


def test_assert_can_transition_raises_for_disallowed():
    with pytest.raises(InvalidTransition):
        assert_can_transition(OrderStatus.PENDING_PAYMENT, OrderStatus.COMPLETED)
    with pytest.raises(InvalidTransition):
        assert_can_transition(OrderStatus.REFUNDED, OrderStatus.PAID)


def test_assert_can_transition_passes_for_allowed():
    assert_can_transition(OrderStatus.PENDING_PAYMENT, OrderStatus.PAID)
    assert_can_transition(OrderStatus.PAID, OrderStatus.PENDING_REFUND)
    assert_can_transition(OrderStatus.PENDING_REFUND, OrderStatus.REFUNDED)
