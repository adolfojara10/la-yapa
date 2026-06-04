"""Shared webhook dispatch logic.

Verification order (any failure → reject without leaking which check failed):
    1. IP allowlist (skipped in dev when list empty)
    2. HMAC signature verify
    3. Replay window (event age <= WEBHOOK_REPLAY_WINDOW_SECONDS)
    4. Idempotency (dedupe by WebhookEventLog (provider, provider_event_id))

On payment.succeeded: order → PAID, push notification dispatched.
On payment.failed: order → CANCELLED, inventory restored.
On refund.succeeded: order → REFUNDED.
On refund.failed: leave order in PENDING_REFUND, mark refund_failed_at.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.orders.models import CancelledBy, Order, OrderStatus
from apps.orders.services import cancel_order, mark_paid
from apps.orders.state_machine import assert_can_transition

from .ip_allowlist import is_allowed, remote_ip_from_request
from .models import (
    PaymentStatus,
    PaymentTransaction,
    WebhookEventLog,
)
from .providers import get_provider
from .providers.base import WebhookEvent
from .providers.exceptions import (
    ProviderError,
    SignatureInvalidError,
)

logger = logging.getLogger(__name__)


class WebhookRejected(Exception):
    """Wrapper for any pre-dispatch verification failure. The view layer
    returns 401 + a generic message regardless of `.code` (we don't leak
    which check failed to a probing attacker)."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def handle_webhook_request(*, provider_name: str, request) -> WebhookEventLog | None:
    """Top-level entry called by the views. Returns the persisted log row,
    or None if the event was a duplicate (already processed)."""

    raw_body = request.body
    headers = dict(request.headers.items())
    remote_ip = remote_ip_from_request(request)

    if not is_allowed(provider_name, remote_ip):
        raise WebhookRejected("ip_not_allowlisted")

    try:
        provider = get_provider(provider_name)
    except (ValueError, ProviderError) as exc:
        logger.exception("Provider lookup failed for %s", provider_name)
        raise WebhookRejected("provider_misconfigured") from exc

    try:
        event = provider.parse_event(raw_body, headers)
    except SignatureInvalidError as exc:
        raise WebhookRejected("invalid_signature") from exc
    except ProviderError as exc:
        logger.warning("Webhook parse failed: %s", exc)
        raise WebhookRejected("invalid_payload") from exc

    replay_window = int(getattr(settings, "PAYMENT_WEBHOOK_REPLAY_WINDOW_SECONDS", 600))
    if event.age_seconds > replay_window:
        raise WebhookRejected("replay_window_exceeded")

    # Idempotency: dedupe by (provider, event_id). Race-safe via the
    # unique constraint — concurrent webhooks for the same event collapse
    # to a single insert.
    with transaction.atomic():
        if WebhookEventLog.objects.filter(
            provider=provider_name, provider_event_id=event.event_id
        ).exists():
            return None
        log = WebhookEventLog.objects.create(
            provider=provider_name,
            provider_event_id=event.event_id,
            event_type=event.event_type,
            received_ip=remote_ip or None,
            payload=event.raw,
        )

    _dispatch_event(provider_name, event)
    return log


# ---- internals ------------------------------------------------------------


def _dispatch_event(provider_name: str, event: WebhookEvent) -> None:
    """Apply the event to the matching PaymentTransaction + Order."""
    try:
        tx = PaymentTransaction.objects.select_related("order").get(
            provider=provider_name,
            provider_transaction_id=event.provider_transaction_id,
        )
    except PaymentTransaction.DoesNotExist:
        logger.warning(
            "Webhook for unknown tx %s/%s — ignoring",
            provider_name,
            event.provider_transaction_id,
        )
        return

    order = tx.order

    if event.event_type == "payment.succeeded":
        _on_payment_succeeded(order, tx, event)
    elif event.event_type == "payment.failed":
        _on_payment_failed(order, tx, event)
    elif event.event_type == "refund.succeeded":
        _on_refund_succeeded(order, tx, event)
    elif event.event_type == "refund.failed":
        _on_refund_failed(order, tx, event)
    else:
        logger.info("Unhandled webhook event type: %s", event.event_type)


@transaction.atomic
def _on_payment_succeeded(order: Order, tx: PaymentTransaction, event: WebhookEvent) -> None:
    tx.status = PaymentStatus.SUCCESS
    tx.raw_response = {**(tx.raw_response or {}), "succeeded": event.raw}
    tx.save(update_fields=["status", "raw_response", "updated_at"])

    if order.status == OrderStatus.PAID:
        return  # already processed

    mark_paid(order, payment_method=tx.provider, provider_ref=tx.provider_transaction_id)

    # Suspended-meal donation: if the consumer ticked the toggle at checkout,
    # spin up a donation now that funds have settled.
    if order.donate_as_suspended_meal:
        from apps.suspended_meals.models import SuspendedMealDonation

        SuspendedMealDonation.objects.create(
            donor=order.consumer,
            amount=order.total_paid,
            bag=order.bag,
            is_anonymous=True,
        )

    # Push notification — non-fatal if dispatcher fails.
    try:
        from apps.notifications.services import send_push

        send_push(
            order.consumer,
            title="¡Pago confirmado! 🌱",
            body=f"Tu código de retiro: {order.pickup_code}",
            data={"order_id": str(order.id), "type": "order_paid"},
            category="order_updates",
        )
    except Exception:
        logger.exception("Push notification dispatch failed for order %s", order.id)


@transaction.atomic
def _on_payment_failed(order: Order, tx: PaymentTransaction, event: WebhookEvent) -> None:
    tx.status = PaymentStatus.FAILED
    tx.raw_response = {**(tx.raw_response or {}), "failed": event.raw}
    tx.save(update_fields=["status", "raw_response", "updated_at"])

    if order.status != OrderStatus.PENDING_PAYMENT:
        return  # already terminal

    # Use the cancel service to also restore inventory.
    try:
        cancel_order(order=order, actor=CancelledBy.SYSTEM, reason="payment_failed")
    except Exception:
        logger.exception("Failed to cancel order %s after payment failure", order.id)


@transaction.atomic
def _on_refund_succeeded(order: Order, tx: PaymentTransaction, event: WebhookEvent) -> None:
    tx.status = PaymentStatus.REFUNDED
    tx.refunded_at = timezone.now()
    raw_amount = event.amount
    if raw_amount is not None:
        tx.refund_amount = Decimal(str(raw_amount))
    tx.raw_response = {**(tx.raw_response or {}), "refund_succeeded": event.raw}
    tx.save(update_fields=["status", "refunded_at", "refund_amount", "raw_response", "updated_at"])

    if order.status == OrderStatus.REFUNDED:
        return
    if order.status == OrderStatus.PENDING_REFUND:
        assert_can_transition(order.status, OrderStatus.REFUNDED)
        order.status = OrderStatus.REFUNDED
        order.save(update_fields=["status", "updated_at"])


@transaction.atomic
def _on_refund_failed(order: Order, tx: PaymentTransaction, event: WebhookEvent) -> None:
    tx.status = PaymentStatus.REFUND_FAILED
    tx.raw_response = {**(tx.raw_response or {}), "refund_failed": event.raw}
    tx.save(update_fields=["status", "raw_response", "updated_at"])

    Order.objects.filter(pk=order.pk).update(
        refund_failed_at=timezone.now(),
        updated_at=timezone.now(),
    )
