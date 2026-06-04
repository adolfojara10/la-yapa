"""Payment service layer — process_payment, refund_payment, bonus credit ops.

These are the only entry points the view + webhook layers should call. The
provider abstraction lives in `providers/`; this module owns the DB writes
that pair with provider calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order, OrderStatus
from apps.orders.state_machine import assert_can_transition

from .models import (
    BonusCredit,
    PaymentStatus,
    PaymentTransaction,
)
from .providers import get_provider
from .providers.base import ChargeSession
from .providers.exceptions import (
    ProviderError,
    RefundFailedError,
)

# ---- public surface --------------------------------------------------------


@dataclass
class ChargeContext:
    session: ChargeSession
    transaction: PaymentTransaction


class PaymentError(Exception):
    """Raised by service-layer payment failures (provider configured but call failed)."""

    def __init__(self, message: str, *, code: str = "payment_error"):
        super().__init__(message)
        self.code = code


class CreditError(Exception):
    def __init__(self, message: str, *, code: str = "credit_error"):
        super().__init__(message)
        self.code = code


@transaction.atomic
def process_payment(
    *,
    order: Order,
    provider_name: str,
    return_url: str,
) -> ChargeContext:
    """Create a payment session with the provider, persist the pending
    transaction. Returns the session details for the mobile client.

    Idempotent on the order: if the order already has a PENDING transaction
    on the same provider, the existing session is returned (so the user can
    re-tap "Pay" without creating duplicate sessions).
    """
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise PaymentError(f"Order in {order.status}, cannot charge", code="invalid_status")

    provider = get_provider(provider_name)
    try:
        session = provider.create_charge(order, return_url=return_url)
    except ProviderError as exc:
        raise PaymentError(f"Provider failed to create charge: {exc}", code=exc.code) from exc

    tx = PaymentTransaction.objects.create(
        order=order,
        provider=provider_name,
        provider_transaction_id=session.provider_transaction_id,
        amount=session.amount,
        status=PaymentStatus.PENDING,
        raw_response={"session_id": session.session_id, "webview_url": session.webview_url},
    )
    return ChargeContext(session=session, transaction=tx)


def refund_payment(order: Order, *, reason: str = "") -> None:
    """Trigger a refund against the most recent SUCCESS transaction on `order`.

    In this session we run synchronously inline (post-commit hook from
    cancel_order). Phase 2 moves this to a Celery task with retries.

    The Order is already in PENDING_REFUND when we land here. On success we
    flip to REFUNDED; on failure we set `refund_failed_at` for ops alerting
    but leave status as PENDING_REFUND (consumer-facing message is the same).
    """
    tx = (
        PaymentTransaction.objects.filter(order=order, status=PaymentStatus.SUCCESS)
        .order_by("-created_at")
        .first()
    )
    if tx is None:
        # No captured tx — nothing to refund. Flip straight to CANCELLED.
        with transaction.atomic():
            fresh = Order.objects.select_for_update().get(pk=order.pk)
            if fresh.status == OrderStatus.PENDING_REFUND:
                assert_can_transition(fresh.status, OrderStatus.CANCELLED)
                fresh.status = OrderStatus.CANCELLED
                fresh.save(update_fields=["status", "updated_at"])
        return

    provider = get_provider(tx.provider)
    try:
        result = provider.refund(
            provider_transaction_id=tx.provider_transaction_id, amount=tx.amount
        )
    except RefundFailedError as exc:
        _mark_refund_failed(order, tx, str(exc))
        return
    except ProviderError as exc:
        _mark_refund_failed(order, tx, f"Provider error: {exc}")
        return

    with transaction.atomic():
        tx.refund_provider_transaction_id = result.refund_provider_transaction_id
        tx.refund_amount = tx.amount
        tx.raw_response = {**(tx.raw_response or {}), "refund": result.raw_response}
        if result.status == "success":
            tx.status = PaymentStatus.REFUNDED
            tx.refunded_at = timezone.now()
        elif result.status == "pending":
            tx.status = PaymentStatus.REFUND_PENDING
        else:
            tx.status = PaymentStatus.REFUND_FAILED
        tx.save()

        # Order status update only on success. Pending refunds wait for the
        # webhook to flip to REFUNDED. Failed refunds bubble to ops.
        if result.status == "success":
            fresh = Order.objects.select_for_update().get(pk=order.pk)
            if fresh.status == OrderStatus.PENDING_REFUND:
                assert_can_transition(fresh.status, OrderStatus.REFUNDED)
                fresh.status = OrderStatus.REFUNDED
                fresh.save(update_fields=["status", "updated_at"])
        elif result.status == "failed":
            _mark_refund_failed(order, tx, "Provider returned failed status")


def _mark_refund_failed(order: Order, tx: PaymentTransaction, reason: str) -> None:
    with transaction.atomic():
        tx.status = PaymentStatus.REFUND_FAILED
        tx.raw_response = {**(tx.raw_response or {}), "refund_failure": reason}
        tx.save(update_fields=["status", "raw_response", "updated_at"])
        Order.objects.filter(pk=order.pk).update(
            refund_failed_at=timezone.now(),
            updated_at=timezone.now(),
        )


# ---- bonus credit ---------------------------------------------------------


@transaction.atomic
def apply_bonus_credit(*, order: Order, credit_id: int) -> Decimal:
    """Apply a BonusCredit to a pending_payment order, recompute total_paid.

    Returns the applied credit amount. Raises CreditError on any rule
    violation.
    """
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise CreditError(
            "Bonus credit can only be applied while order is pending payment",
            code="invalid_status",
        )
    try:
        credit = BonusCredit.objects.select_for_update().get(pk=credit_id)
    except BonusCredit.DoesNotExist as exc:
        raise CreditError("Credit not found", code="credit_not_found") from exc

    if credit.user_id != order.consumer_id:
        raise CreditError("Credit does not belong to this consumer", code="credit_wrong_user")
    if credit.is_redeemed:
        raise CreditError("Credit already redeemed", code="credit_already_redeemed")
    if credit.is_expired:
        raise CreditError("Credit has expired", code="credit_expired")

    gross = order.sale_price_snapshot * order.quantity
    applied = min(credit.amount, gross)
    new_total = max(gross - applied, Decimal("0"))

    order.applied_credit_amount = applied
    order.total_paid = new_total
    # Commission + payout amounts recompute against the *gross* sale (the
    # business is paid out of the original sale; the credit comes from the
    # platform's pocket, not the business's).
    order.save(
        update_fields=[
            "applied_credit_amount",
            "total_paid",
            "updated_at",
        ]
    )

    credit.redeemed_in_order = order
    credit.redeemed_at = timezone.now()
    credit.save(update_fields=["redeemed_in_order", "redeemed_at", "updated_at"])
    return applied
