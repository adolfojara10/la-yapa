"""Order service layer — create / cancel / complete / expire.

All write paths go through here, not through direct `Order.objects.create()` or
manual `order.status = ...`. The state machine is enforced at every transition
via `assert_can_transition`.

Exceptions raised here are the public surface for views / Celery tasks; the
view layer maps them to HTTP responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.bags.models import Bag

from .models import CancelledBy, Order, OrderStatus
from .state_machine import assert_can_transition

# ---- exceptions ------------------------------------------------------------


class OrderServiceError(Exception):
    """Base for order-service-level errors. `.code` is a stable string the
    view layer surfaces to clients (and tests assert on)."""

    code: str = "order_service_error"

    def __init__(self, message: str = "", code: str | None = None):
        super().__init__(message or self.code)
        if code:
            self.code = code


class BagUnavailable(OrderServiceError):
    code = "bag_unavailable"


class InsufficientStock(OrderServiceError):
    code = "insufficient_stock"


class CancellationNotAllowed(OrderServiceError):
    code = "cancellation_not_allowed"


class CancellationOutsideWindow(OrderServiceError):
    code = "cancellation_outside_window"


# ----- pickup-time errors -----


class PickupError(OrderServiceError):
    """Base for confirm_pickup_* failures."""

    code = "pickup_error"


class QrInvalid(PickupError):
    code = "qr_invalid"


class PinInvalid(PickupError):
    code = "pin_invalid"


class PinLocked(PickupError):
    code = "pin_locked"


class OutsidePickupWindow(PickupError):
    code = "outside_pickup_window"


class PickupInvalidStatus(PickupError):
    code = "pickup_invalid_status"


# ---- result types ----------------------------------------------------------


@dataclass
class CancelResult:
    order: Order
    triggered_refund: bool
    granted_bonus_credit_id: int | None = None


# ---- public service functions ---------------------------------------------


@transaction.atomic
def create_order(
    *,
    consumer,
    bag_id: str,
    quantity: int = 1,
    donate_as_suspended_meal: bool = False,
) -> Order:
    """Reserve `quantity` units of `bag_id` for `consumer` in a single
    transaction. Returns an Order in PENDING_PAYMENT status.

    The Bag row is locked via SELECT FOR UPDATE so two simultaneous orders
    for the last unit cannot both succeed. The loser raises InsufficientStock.

    Inventory is decremented HERE (not on payment success) so the bag count
    on the discovery list immediately reflects the reservation. If the
    payment never completes, `expire_stale_pending` restores it.
    """
    if quantity < 1:
        raise OrderServiceError("Quantity must be at least 1", code="invalid_quantity")

    try:
        bag = (
            Bag.objects.select_for_update()
            .select_related("business_location__business")
            .get(pk=bag_id)
        )
    except Bag.DoesNotExist as exc:
        raise BagUnavailable("Bag not found") from exc

    now = timezone.now()
    if not bag.is_active:
        raise BagUnavailable("Bag is not active")
    if bag.pickup_window_end <= now:
        raise BagUnavailable("Pickup window has closed")
    if bag.quantity_available < quantity:
        raise InsufficientStock(
            f"Only {bag.quantity_available} units available, you requested {quantity}"
        )

    bag.quantity_available -= quantity
    bag.save(update_fields=["quantity_available", "updated_at"])

    sale_price = bag.sale_price
    original_price = bag.original_price
    total_paid = (sale_price * quantity).quantize(Decimal("0.01"))
    commission_rate = bag.business_location.business.commission_rate
    platform_commission = (total_paid * commission_rate).quantize(Decimal("0.01"))
    business_payout_amount = (total_paid - platform_commission).quantize(Decimal("0.01"))

    order = Order.objects.create(
        consumer=consumer,
        bag=bag,
        business_location=bag.business_location,
        quantity=quantity,
        original_price_snapshot=original_price,
        sale_price_snapshot=sale_price,
        total_paid=total_paid,
        platform_commission=platform_commission,
        business_payout_amount=business_payout_amount,
        status=OrderStatus.PENDING_PAYMENT,
        donate_as_suspended_meal=donate_as_suspended_meal,
    )
    return order


@transaction.atomic
def mark_paid(order: Order, *, payment_method: str, provider_ref: str) -> Order:
    """Webhook entry point: provider has confirmed the payment is captured."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status == OrderStatus.PAID:
        # Idempotent: webhooks can fire twice.
        return order
    assert_can_transition(order.status, OrderStatus.PAID)
    order.status = OrderStatus.PAID
    order.payment_method = payment_method
    order.payment_provider_ref = provider_ref
    order.save(
        update_fields=[
            "status",
            "payment_method",
            "payment_provider_ref",
            "updated_at",
        ]
    )
    return order


@transaction.atomic
def cancel_order(
    *,
    order: Order,
    actor: str,
    reason: str = "",
) -> CancelResult:
    """Cancel an order. Routing depends on:
      - actor: consumer / business / admin / system
      - current status: pre-paid → straight to CANCELLED;
                        paid → PENDING_REFUND + provider refund call

    Consumer cancellations enforce the 1h-before-pickup window. Business
    cancellations grant a $1 BonusCredit to the consumer (per spec).
    """
    if actor not in CancelledBy.values:
        raise OrderServiceError(f"Unknown actor {actor!r}", code="invalid_actor")

    order = Order.objects.select_for_update().select_related("bag").get(pk=order.pk)

    if order.is_terminal:
        raise CancellationNotAllowed(f"Order already {order.status}")

    if actor == CancelledBy.CONSUMER and not order.is_within_consumer_cancel_window():
        raise CancellationOutsideWindow("Cancellation window closes 1 hour before pickup.")

    # Restore inventory — both pre-paid and paid cancellations free up the
    # bag count immediately. F-expr avoids race with concurrent writers.
    Bag.objects.filter(pk=order.bag_id).update(
        quantity_available=F("quantity_available") + order.quantity,
        updated_at=timezone.now(),
    )

    now = timezone.now()
    order.cancelled_by = actor
    order.cancelled_at = now
    order.cancellation_reason = reason

    triggered_refund = False
    if order.status in (OrderStatus.PAID, OrderStatus.READY_FOR_PICKUP):
        assert_can_transition(order.status, OrderStatus.PENDING_REFUND)
        order.status = OrderStatus.PENDING_REFUND
        triggered_refund = True
    else:
        # pending_payment never captured funds → straight to CANCELLED.
        assert_can_transition(order.status, OrderStatus.CANCELLED)
        order.status = OrderStatus.CANCELLED

    order.save(
        update_fields=[
            "status",
            "cancelled_by",
            "cancelled_at",
            "cancellation_reason",
            "updated_at",
        ]
    )

    granted_credit_id = None
    if actor == CancelledBy.BUSINESS:
        from apps.payments.models import (
            BonusCredit,
            BonusCreditSource,
            Payout,
            PayoutLineItem,
            PayoutLineItemType,
        )

        bonus_amount = Decimal(str(getattr(settings, "BUSINESS_CANCELLATION_BONUS_AMOUNT", "1.00")))
        credit_ttl_days = int(getattr(settings, "BUSINESS_CANCELLATION_BONUS_TTL_DAYS", 90))
        credit = BonusCredit.objects.create(
            user=order.consumer,
            amount=bonus_amount,
            source=BonusCreditSource.BUSINESS_CANCELLATION,
            source_business=order.business_location.business,
            source_order=order,
            expires_at=now + timedelta(days=credit_ttl_days),
            notes=f"Compensation for cancelled order {order.id}",
        )
        granted_credit_id = credit.id

        # Record the obligation against the business's next payout. We
        # attach to the most recent OPEN payout if one exists, otherwise
        # leave the line item unattached (next payout job picks it up by
        # business + status). For MVP we just create a PENDING Payout
        # placeholder if none exists. Real payout scheduling is Phase 2.
        payout = (
            Payout.objects.filter(
                business=order.business_location.business,
                status="pending",
            )
            .order_by("-created_at")
            .first()
        )
        if payout is None:
            payout = Payout.objects.create(
                business=order.business_location.business,
                period_start=now,
                period_end=now + timedelta(days=7),
            )
        PayoutLineItem.objects.create(
            payout=payout,
            order=order,
            amount=-bonus_amount,
            type=PayoutLineItemType.BONUS_CREDIT_DEDUCTION,
        )

    # Trigger refund AFTER the transaction is solid. Dispatched to Celery
    # so a slow provider call doesn't block the HTTP request that cancelled
    # the order. Under tests (CELERY_TASK_ALWAYS_EAGER=True) the task
    # runs synchronously inline; in prod a worker picks it up.
    if triggered_refund:
        # Imported inline to avoid a circular dep at module load.
        from apps.payments.tasks import refund_payment_task

        order_pk = str(order.pk)
        transaction.on_commit(
            lambda: refund_payment_task.apply_async(args=[order_pk], kwargs={"reason": reason})
        )

    return CancelResult(
        order=order,
        triggered_refund=triggered_refund,
        granted_bonus_credit_id=granted_credit_id,
    )


@transaction.atomic
def complete_order(*, order: Order) -> Order:
    """Business confirmed pickup. Flips to COMPLETED; the ImpactStat signal
    (apps.impact.signals) picks it up."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status == OrderStatus.COMPLETED:
        return order
    assert_can_transition(order.status, OrderStatus.COMPLETED)
    order.status = OrderStatus.COMPLETED
    order.picked_up_at = timezone.now()
    order.save(update_fields=["status", "picked_up_at", "updated_at"])
    return order


@transaction.atomic
def expire_stale_pending(*, older_than_minutes: int = 15) -> int:
    """Cron entry point: cancels pending_payment orders that have been
    sitting unpaid for too long. Returns count of orders expired.

    Inventory is restored for each. Safe to run repeatedly.
    """
    cutoff = timezone.now() - timedelta(minutes=older_than_minutes)
    stale = list(
        Order.objects.select_for_update()
        .filter(status=OrderStatus.PENDING_PAYMENT, created_at__lt=cutoff)
        .values_list("id", "bag_id", "quantity")
    )
    if not stale:
        return 0

    # Restore inventory in one pass.
    from collections import defaultdict

    per_bag: defaultdict[str, int] = defaultdict(int)
    for _id, bag_id, qty in stale:
        per_bag[bag_id] += qty
    for bag_id, qty in per_bag.items():
        Bag.objects.filter(pk=bag_id).update(
            quantity_available=F("quantity_available") + qty,
            updated_at=timezone.now(),
        )

    Order.objects.filter(id__in=[oid for oid, _, _ in stale]).update(
        status=OrderStatus.EXPIRED,
        updated_at=timezone.now(),
    )
    return len(stale)


# ---------------------------------------------------------------------------
# Pickup confirmation — business-side.
#
# Two entry points: confirm_pickup_by_qr (scanner path) and
# confirm_pickup_by_pin (manual entry fallback). Both share the same
# downstream invariants: order must belong to one of the requester's owned
# business locations, status must be PAID, pickup window must be open
# (within the configured grace band), QR must not be already consumed.
#
# On success: status → COMPLETED, picked_up_at set, qr_consumed_at set
# AND pickup_qr_token rotated to a fresh UUID. The old token is no longer
# in the DB — second scan of the original returns QrInvalid, indistinguishable
# from a forged token.
# ---------------------------------------------------------------------------


def _owned_business_location_ids(business_owner) -> list[int]:
    """All BusinessLocation IDs belonging to businesses owned by this user."""
    from apps.businesses.models import BusinessLocation

    return list(
        BusinessLocation.objects.filter(business__owner=business_owner).values_list("id", flat=True)
    )


def _assert_confirm_preconditions(order: Order) -> None:
    """Shared invariants for both QR and PIN paths."""
    if order.status == OrderStatus.COMPLETED:
        # Idempotent: re-confirming a completed order is a no-op (caller
        # discovers this from the returned status). We don't raise here.
        return
    if order.status != OrderStatus.PAID:
        raise PickupInvalidStatus(f"Order in {order.status}, only PAID orders can be confirmed.")
    if not order.is_within_pickup_window():
        raise OutsidePickupWindow(
            "Pickup attempted outside the allowed window (60min early / 15min late grace)."
        )


@transaction.atomic
def confirm_pickup_by_qr(*, business_owner, qr_token: str) -> Order:
    """Look up the order by single-use qr_token, verify ownership + window,
    flip to COMPLETED, rotate the token.

    Single-use enforcement: after a successful confirm, pickup_qr_token is
    replaced with a fresh UUID. A replay of the original token finds no
    matching row and raises QrInvalid — same response as a forged token,
    so a scanner-equipped attacker can't tell which case they're in.
    """
    if not qr_token:
        raise QrInvalid()

    owned_location_ids = _owned_business_location_ids(business_owner)
    if not owned_location_ids:
        # User owns no businesses; can't confirm anyone's pickup.
        raise QrInvalid()

    try:
        order = (
            Order.objects.select_for_update()
            .select_related("bag", "consumer", "business_location__business")
            .get(
                pickup_qr_token=qr_token,
                business_location_id__in=owned_location_ids,
            )
        )
    except (Order.DoesNotExist, ValueError):
        # ValueError catches malformed UUID inputs.
        raise QrInvalid() from None

    _assert_confirm_preconditions(order)
    if order.status == OrderStatus.COMPLETED:
        return order

    # Flip status, mark consumed, rotate.
    import uuid as _uuid

    assert_can_transition(order.status, OrderStatus.COMPLETED)
    order.status = OrderStatus.COMPLETED
    order.picked_up_at = timezone.now()
    order.qr_consumed_at = timezone.now()
    order.pickup_qr_token = _uuid.uuid4()
    order.save(
        update_fields=[
            "status",
            "picked_up_at",
            "qr_consumed_at",
            "pickup_qr_token",
            "updated_at",
        ]
    )
    return order


def confirm_pickup_by_pin(
    *,
    business_owner,
    business_location_id: int,
    pin: str,
) -> Order:
    """Look up the active order at `business_location_id` with this `pin`,
    verify ownership + window, flip to COMPLETED.

    PIN is only unique within a business location's active orders. Caller
    must supply the location explicitly (the vendor knows which location
    they're working at — it's the one they're logged in for).

    Attempt tracking is per-order: lookup the most recent matching PAID
    order, increment pin_attempts on validation miss (in a separate
    transaction so the bump persists even when we then raise PinInvalid),
    lock at PIN_MAX_ATTEMPTS. Once locked, even the correct PIN returns
    PinLocked; QR scan still works as the bypass path.

    This function is NOT wrapped in @transaction.atomic at the outer
    boundary because the success / failure paths have different commit
    semantics — see inline atomic blocks.
    """
    if not pin or len(pin) != 4 or not pin.isdigit():
        raise PinInvalid()

    owned_location_ids = _owned_business_location_ids(business_owner)
    if business_location_id not in owned_location_ids:
        # Same opaque response as PIN-not-found: don't leak which locations
        # belong to which owner.
        raise PinInvalid()

    with transaction.atomic():
        # Candidate: any PAID order at this location whose pickup_code matches.
        # In rare cases there could be multiple — pick the one whose pickup
        # window is currently open (else fall back to the first).
        candidates = list(
            Order.objects.select_for_update()
            .filter(
                business_location_id=business_location_id,
                pickup_code=pin,
                status=OrderStatus.PAID,
            )
            .select_related("bag", "consumer")
            .order_by("bag__pickup_window_start")
        )

        if not candidates:
            # No matching PAID order. A guess against a non-existent PIN
            # costs nothing — we can't bump a counter on "no row" without
            # leaking PIN existence. The 5-attempt cap protects a SPECIFIC
            # known order from PIN guessing once an attacker knows it exists
            # (e.g. shoulder-surfed the order screen). Acceptable tradeoff.
            raise PinInvalid()

        order = next(
            (o for o in candidates if o.is_within_pickup_window()),
            candidates[0],
        )

        # Lock check first — a locked order is unreachable via PIN even
        # with the correct code. QR scan path still works.
        if order.is_pin_locked:
            raise PinLocked()

        # Window failure is NOT a PIN miss — don't bump the counter.
        # The PIN was right; the timing was wrong.
        _assert_confirm_preconditions(order)

        if order.status == OrderStatus.COMPLETED:
            return order

        # PIN matched + all preconditions OK → flip.
        import uuid as _uuid

        assert_can_transition(order.status, OrderStatus.COMPLETED)
        order.status = OrderStatus.COMPLETED
        order.picked_up_at = timezone.now()
        order.qr_consumed_at = timezone.now()
        order.pickup_qr_token = _uuid.uuid4()
        order.save(
            update_fields=[
                "status",
                "picked_up_at",
                "qr_consumed_at",
                "pickup_qr_token",
                "updated_at",
            ]
        )
        return order


def register_pin_miss(*, business_owner, business_location_id: int, pin: str) -> None:
    """Increment pin_attempts on the matching PAID order; lock at cap.

    Called by the VIEW after confirm_pickup_by_pin raises PinInvalid, so
    the counter bump runs in a fresh transaction (not rolled back with
    the failed confirm). No-op if:
      - PIN is malformed
      - business_location is not owned by the caller (sealing the
        cross-business remote-lock attack vector)
      - no PAID order matches the PIN at the location
    """
    if not pin or len(pin) != 4 or not pin.isdigit():
        return
    owned_location_ids = _owned_business_location_ids(business_owner)
    if business_location_id not in owned_location_ids:
        return

    with transaction.atomic():
        order = (
            Order.objects.select_for_update()
            .filter(
                business_location_id=business_location_id,
                pickup_code=pin,
                status=OrderStatus.PAID,
            )
            .order_by("bag__pickup_window_start")
            .first()
        )
        if order is None or order.is_pin_locked:
            return

        new_attempts = order.pin_attempts + 1
        order.pin_attempts = new_attempts
        update_fields = ["pin_attempts", "updated_at"]
        if new_attempts >= Order.PIN_MAX_ATTEMPTS:
            order.pin_locked_at = timezone.now()
            update_fields.append("pin_locked_at")
        order.save(update_fields=update_fields)
