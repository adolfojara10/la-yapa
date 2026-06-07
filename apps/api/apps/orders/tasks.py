"""Celery tasks for pickup reminders + stale-order cleanup.

The three pickup-reminder tasks share the same shape: re-read the order
on execution, bail if its status isn't one of {PAID, READY_FOR_PICKUP}
(consumer cancelled / picked up early / refunded), else dispatch a push
to the consumer's registered Expo tokens.

Scheduled per-order from `apps.payments.webhooks._on_payment_succeeded`:

    send_pickup_ready.apply_async(args=[order_id], eta=pickup_start)
    send_pickup_reminder_1h.apply_async(args=[order_id],
                                        eta=pickup_end - timedelta(hours=1))
    send_pickup_reminder_30min.apply_async(args=[order_id],
                                           eta=pickup_end - timedelta(minutes=30))

In test settings we set `CELERY_TASK_ALWAYS_EAGER=True` so these run
synchronously without a worker. apply_async(eta=...) under eager mode
runs IMMEDIATELY (ignores the eta), which is fine for unit tests that
just want to assert the task fires.
"""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


_REMINDER_STATUSES = frozenset({"paid", "ready_for_pickup"})


def _send_for_order(order_id: str, *, title: str, body_template: str) -> int:
    """Shared implementation. Returns number of tokens dispatched."""
    from apps.notifications.services import send_push
    from apps.orders.models import Order

    try:
        order = Order.objects.select_related("consumer", "bag").get(pk=order_id)
    except Order.DoesNotExist:
        logger.info("Pickup reminder skipped — order %s no longer exists", order_id)
        return 0

    if order.status not in _REMINDER_STATUSES:
        logger.info(
            "Pickup reminder skipped for order %s — status=%s",
            order_id,
            order.status,
        )
        return 0

    return send_push(
        order.consumer,
        title=title,
        body=body_template.format(pickup_code=order.pickup_code),
        data={"order_id": str(order.id), "type": "pickup_reminder"},
        category="pickup_reminders",
    )


@shared_task(name="apps.orders.tasks.send_pickup_ready")
def send_pickup_ready(order_id: str) -> int:
    return _send_for_order(
        order_id,
        title="¡Tu bolsa está lista! 🎉",
        body_template="Pasa a retirarla. Código: {pickup_code}",
    )


@shared_task(name="apps.orders.tasks.send_pickup_reminder_1h")
def send_pickup_reminder_1h(order_id: str) -> int:
    return _send_for_order(
        order_id,
        title="Queda 1 hora para retirar tu bolsa",
        body_template="No olvides pasar antes de que cierre. Código: {pickup_code}",
    )


@shared_task(name="apps.orders.tasks.send_pickup_reminder_30min")
def send_pickup_reminder_30min(order_id: str) -> int:
    return _send_for_order(
        order_id,
        title="¡Últimos 30 min para retirar!",
        body_template="Apúrate, la ventana cierra pronto. Código: {pickup_code}",
    )


@shared_task(name="apps.orders.tasks.expire_stale_pending_orders")
def expire_stale_pending_orders() -> int:
    """Hourly beat task: cancel + restore inventory for abandoned orders
    sitting in PENDING_PAYMENT longer than 15 minutes."""
    from apps.orders.services import expire_stale_pending

    count = expire_stale_pending(older_than_minutes=15)
    if count:
        logger.info("Expired %d stale pending_payment orders", count)
    return count
