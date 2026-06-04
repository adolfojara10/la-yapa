"""Allowed Order.status transitions.

The state machine is intentionally small and documented in one place rather
than scattered as `if order.status == ...` checks across services. Any
service that flips status MUST go through `transition()` so a bad transition
fails loudly rather than silently corrupting state.

States:
    pending_payment    Order created, payment session not yet completed.
    paid               Payment webhook confirmed; pickup_code / QR usable.
    ready_for_pickup   Business marked the bag prepared (Phase 2 — not used yet,
                       reserved so the schema is forward-compatible).
    completed          Business confirmed pickup (QR scan or PIN entry).
    pending_refund     Cancel triggered after payment; provider refund in flight.
    cancelled          Terminal — never paid (or payment failed pre-paid).
    refunded           Terminal — refund confirmed by provider.
    expired            Terminal — pending_payment swept by cron after timeout.
"""

from __future__ import annotations

from apps.orders.models import OrderStatus

# (from_status) -> set of allowed to_statuses.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    OrderStatus.PENDING_PAYMENT: frozenset(
        {
            OrderStatus.PAID,
            OrderStatus.CANCELLED,
            OrderStatus.EXPIRED,
        }
    ),
    OrderStatus.PAID: frozenset(
        {
            OrderStatus.READY_FOR_PICKUP,
            OrderStatus.COMPLETED,
            OrderStatus.PENDING_REFUND,
        }
    ),
    OrderStatus.READY_FOR_PICKUP: frozenset(
        {
            OrderStatus.COMPLETED,
            OrderStatus.PENDING_REFUND,
        }
    ),
    OrderStatus.PENDING_REFUND: frozenset(
        {
            OrderStatus.REFUNDED,
            OrderStatus.CANCELLED,  # refund failed; ops resolved
        }
    ),
    # Terminal statuses: no outgoing transitions.
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.REFUNDED: frozenset(),
    OrderStatus.EXPIRED: frozenset(),
}


class InvalidTransition(Exception):
    """Raised when a service tries to move an Order between two statuses
    that aren't connected in the state machine."""

    def __init__(self, current: str, attempted: str):
        super().__init__(f"Cannot transition order from {current!r} to {attempted!r}.")
        self.current = current
        self.attempted = attempted


def assert_can_transition(current: str, target: str) -> None:
    """Raise InvalidTransition if `current -> target` is not in the allowed table."""
    if target not in ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise InvalidTransition(current, target)
