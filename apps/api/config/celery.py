"""Celery application instance + beat schedule."""

from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("layapa")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


# ---------------------------------------------------------------------------
# Beat schedule — periodic tasks.
#
# `expire_stale_pending_orders` runs hourly to sweep `pending_payment`
# orders whose payment session was abandoned > 15 minutes ago. Restores
# inventory + flips status to EXPIRED.
#
# Per-order pickup reminders (1h-before-close, 30min-before-close,
# at-window-open) are scheduled individually with `apply_async(eta=...)`
# from the payment-succeeded webhook handler — no beat entry needed.
# ---------------------------------------------------------------------------
app.conf.beat_schedule = {
    "expire-stale-pending-orders-hourly": {
        "task": "apps.orders.tasks.expire_stale_pending_orders",
        "schedule": crontab(minute=0),  # top of every hour
    },
}
