"""Celery tasks for payment-side async work.

`refund_payment_task` is the async wrapper around
`apps.payments.services.refund_payment`. Used by `cancel_order`'s
`transaction.on_commit` hook so we don't block the HTTP request that
triggered the cancel.

In test settings `CELERY_TASK_ALWAYS_EAGER=True`, so the task runs
synchronously inline — keeps tests deterministic without needing a worker.
"""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="apps.payments.tasks.refund_payment_task")
def refund_payment_task(order_id: str, *, reason: str = "") -> None:
    from apps.orders.models import Order
    from apps.payments.services import refund_payment

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        logger.warning("Refund task: order %s not found", order_id)
        return
    refund_payment(order, reason=reason)
