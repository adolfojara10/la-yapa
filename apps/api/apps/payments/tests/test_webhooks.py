"""Webhook dispatcher: signature, replay, idempotency, dispatch correctness."""

from __future__ import annotations

import json
import time
from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.orders.models import OrderStatus
from apps.payments.models import PaymentStatus, PaymentTransaction, WebhookEventLog
from apps.payments.providers.fake import SIGNATURE_HEADER, FakePaymentProvider


def _signed_payload(payload: dict) -> tuple[bytes, dict[str, str]]:
    body = json.dumps(payload).encode("utf-8")
    return body, FakePaymentProvider.sign(payload)


def _payphone_webhook_url() -> str:
    return reverse("v1:payments:payphone-webhook")


@pytest.fixture
def captured_tx(pending_order):
    tx = PaymentTransaction.objects.create(
        order=pending_order,
        provider="payphone",
        provider_transaction_id="ppx-tx-001",
        amount=pending_order.total_paid,
        status=PaymentStatus.PENDING,
    )
    return tx


@pytest.mark.django_db
def test_webhook_unsigned_request_rejected(captured_tx):
    client = APIClient()
    body = json.dumps({"id": "ev-1", "type": "payment.succeeded", "transaction_id": "ppx-tx-001"})
    response = client.post(_payphone_webhook_url(), data=body, content_type="application/json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_webhook_payment_succeeded_flips_order_to_paid(captured_tx):
    client = APIClient()
    payload = {
        "id": "ev-success-1",
        "type": "payment.succeeded",
        "transaction_id": "ppx-tx-001",
        "amount": str(captured_tx.amount),
        "created_at": int(time.time()),
    }
    body, headers = _signed_payload(payload)
    response = client.post(
        _payphone_webhook_url(),
        data=body,
        content_type="application/json",
        **{f"HTTP_{SIGNATURE_HEADER.replace('-', '_').upper()}": headers[SIGNATURE_HEADER]},
    )
    assert response.status_code == 200
    captured_tx.refresh_from_db()
    assert captured_tx.status == PaymentStatus.SUCCESS
    captured_tx.order.refresh_from_db()
    assert captured_tx.order.status == OrderStatus.PAID


@pytest.mark.django_db
def test_webhook_duplicate_event_is_noop(captured_tx):
    """Same provider_event_id arriving twice is dropped after the first apply."""
    client = APIClient()
    payload = {
        "id": "ev-dup-42",
        "type": "payment.succeeded",
        "transaction_id": captured_tx.provider_transaction_id,
        "amount": str(captured_tx.amount),
        "created_at": int(time.time()),
    }
    body, headers = _signed_payload(payload)
    hdr = {f"HTTP_{SIGNATURE_HEADER.replace('-', '_').upper()}": headers[SIGNATURE_HEADER]}

    first = client.post(_payphone_webhook_url(), data=body, content_type="application/json", **hdr)
    assert first.status_code == 200
    second = client.post(_payphone_webhook_url(), data=body, content_type="application/json", **hdr)
    assert second.status_code == 200  # webhook still 200 to provider (idempotent)
    assert WebhookEventLog.objects.filter(provider_event_id="ev-dup-42").count() == 1


@pytest.mark.django_db
def test_webhook_replayed_old_event_rejected(captured_tx, settings):
    settings.PAYMENT_WEBHOOK_REPLAY_WINDOW_SECONDS = 60
    client = APIClient()
    payload = {
        "id": "ev-stale",
        "type": "payment.succeeded",
        "transaction_id": captured_tx.provider_transaction_id,
        "amount": str(captured_tx.amount),
        "created_at": int(time.time()) - 600,  # 10 min ago
    }
    body, headers = _signed_payload(payload)
    response = client.post(
        _payphone_webhook_url(),
        data=body,
        content_type="application/json",
        **{f"HTTP_{SIGNATURE_HEADER.replace('-', '_').upper()}": headers[SIGNATURE_HEADER]},
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_webhook_payment_failed_cancels_order(captured_tx):
    client = APIClient()
    initial_inventory = captured_tx.order.bag.quantity_available
    payload = {
        "id": "ev-fail-1",
        "type": "payment.failed",
        "transaction_id": captured_tx.provider_transaction_id,
        "amount": "0",
        "created_at": int(time.time()),
    }
    body, headers = _signed_payload(payload)
    response = client.post(
        _payphone_webhook_url(),
        data=body,
        content_type="application/json",
        **{f"HTTP_{SIGNATURE_HEADER.replace('-', '_').upper()}": headers[SIGNATURE_HEADER]},
    )
    assert response.status_code == 200
    captured_tx.refresh_from_db()
    assert captured_tx.status == PaymentStatus.FAILED
    captured_tx.order.refresh_from_db()
    assert captured_tx.order.status == OrderStatus.CANCELLED
    # Inventory restored.
    captured_tx.order.bag.refresh_from_db()
    assert (
        captured_tx.order.bag.quantity_available == initial_inventory + captured_tx.order.quantity
    )


@pytest.mark.django_db
def test_webhook_refund_succeeded_flips_to_refunded(captured_tx):
    captured_tx.status = PaymentStatus.SUCCESS
    captured_tx.save(update_fields=["status"])
    captured_tx.order.status = OrderStatus.PENDING_REFUND
    captured_tx.order.save(update_fields=["status"])

    client = APIClient()
    payload = {
        "id": "ev-refund-1",
        "type": "refund.succeeded",
        "transaction_id": captured_tx.provider_transaction_id,
        "amount": str(captured_tx.amount),
        "created_at": int(time.time()),
    }
    body, headers = _signed_payload(payload)
    response = client.post(
        _payphone_webhook_url(),
        data=body,
        content_type="application/json",
        **{f"HTTP_{SIGNATURE_HEADER.replace('-', '_').upper()}": headers[SIGNATURE_HEADER]},
    )
    assert response.status_code == 200
    captured_tx.refresh_from_db()
    assert captured_tx.status == PaymentStatus.REFUNDED
    assert captured_tx.refunded_at is not None
    assert captured_tx.refund_amount == Decimal(str(captured_tx.amount))
    captured_tx.order.refresh_from_db()
    assert captured_tx.order.status == OrderStatus.REFUNDED


@pytest.mark.django_db
def test_webhook_unknown_transaction_ignored_silently(consumer):
    """A webhook for a tx we don't have is logged and returns 200."""
    client = APIClient()
    payload = {
        "id": "ev-unknown",
        "type": "payment.succeeded",
        "transaction_id": "ghost-tx-id",
        "amount": "5",
        "created_at": int(time.time()),
    }
    body, headers = _signed_payload(payload)
    response = client.post(
        _payphone_webhook_url(),
        data=body,
        content_type="application/json",
        **{f"HTTP_{SIGNATURE_HEADER.replace('-', '_').upper()}": headers[SIGNATURE_HEADER]},
    )
    # We acknowledge the event (recorded), but no transaction state changes.
    assert response.status_code == 200
    assert WebhookEventLog.objects.filter(provider_event_id="ev-unknown").exists()
