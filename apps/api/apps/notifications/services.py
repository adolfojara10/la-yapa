"""Expo push notification dispatcher.

Plain HTTP call to Expo's push API — no SDK required. Honors per-user
NotificationPreference flags. Token errors deactivate the offending row.

Phase 2: move to Celery for async + batching + retry. For now we're called
from a webhook handler, so synchronous is fine.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from .models import NotificationPreference, PushToken

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_push(
    user,
    *,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
    category: str = "order_updates",
) -> int:
    """Send `title`/`body` to all active push tokens for `user`.

    `category` matches a NotificationPreference field name. If False on the
    preference row, returns 0 without dispatch. Returns the count of tokens
    actually pushed to.
    """
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    if not getattr(prefs, category, True):
        return 0

    tokens = list(PushToken.objects.filter(user=user, is_active=True).values_list("id", "token"))
    if not tokens:
        return 0

    messages = [
        {
            "to": token,
            "title": title,
            "body": body,
            "data": data or {},
            "sound": "default",
        }
        for _, token in tokens
    ]

    try:
        response = requests.post(EXPO_PUSH_URL, json=messages, timeout=10)
        response.raise_for_status()
        body_json = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("Expo push dispatch failed: %s", exc)
        return 0

    # Expo returns either a list of receipts or {"data": [...]}.
    receipts = body_json.get("data", body_json)
    if isinstance(receipts, list):
        for (token_id, _token), receipt in zip(tokens, receipts, strict=False):
            if isinstance(receipt, dict) and receipt.get("status") == "error":
                details = receipt.get("details", {}) or {}
                if details.get("error") == "DeviceNotRegistered":
                    PushToken.objects.filter(pk=token_id).update(is_active=False)

    return len(tokens)
