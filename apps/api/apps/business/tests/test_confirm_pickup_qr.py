"""Pickup confirmation via QR scan."""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.orders.models import OrderStatus


@pytest.mark.django_db
def test_qr_scan_happy_path_completes_order(authed, paid_order):
    qr = str(paid_order.pickup_qr_token)
    response = authed.post(
        reverse("v1:business:confirm-pickup-by-scan"),
        {"qr_token": qr},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    paid_order.refresh_from_db()
    assert paid_order.status == OrderStatus.COMPLETED
    assert paid_order.picked_up_at is not None
    assert paid_order.qr_consumed_at is not None
    # QR token rotated — old value no longer present.
    assert str(paid_order.pickup_qr_token) != qr


@pytest.mark.django_db
def test_qr_replay_returns_404(authed, paid_order):
    qr = str(paid_order.pickup_qr_token)
    url = reverse("v1:business:confirm-pickup-by-scan")
    first = authed.post(url, {"qr_token": qr}, format="json")
    assert first.status_code == 200
    # Second scan of the original token → not found (rotation moved the
    # token; original value no longer matches any row).
    second = authed.post(url, {"qr_token": qr}, format="json")
    assert second.status_code == 404
    assert second.json()["code"] == "qr_invalid"


@pytest.mark.django_db
def test_qr_forged_token_returns_404(authed):
    response = authed.post(
        reverse("v1:business:confirm-pickup-by-scan"),
        {"qr_token": str(uuid.uuid4())},
        format="json",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_qr_for_other_owners_order_returns_404(api_client, paid_order):
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.users.factories import BusinessOwnerFactory

    other = BusinessOwnerFactory(is_email_verified=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other).access_token}")
    response = api_client.post(
        reverse("v1:business:confirm-pickup-by-scan"),
        {"qr_token": str(paid_order.pickup_qr_token)},
        format="json",
    )
    # Owner mismatch → 404 (not 403), per "don't leak existence" rule.
    assert response.status_code == 404


@pytest.mark.django_db
def test_qr_outside_pickup_window_returns_409(authed, paid_order):
    # Push the window into the future beyond the 60min early grace.
    bag = paid_order.bag
    bag.pickup_window_start = timezone.now() + timedelta(hours=4)
    bag.pickup_window_end = timezone.now() + timedelta(hours=6)
    bag.save(update_fields=["pickup_window_start", "pickup_window_end"])

    response = authed.post(
        reverse("v1:business:confirm-pickup-by-scan"),
        {"qr_token": str(paid_order.pickup_qr_token)},
        format="json",
    )
    assert response.status_code == 409
    assert response.json()["code"] == "outside_pickup_window"


@pytest.mark.django_db
def test_qr_within_60min_early_grace_succeeds(authed, paid_order):
    """Vendor confirms a pickup 45 min before window opens — should succeed
    (we deliberately allow up to 60 min early)."""
    bag = paid_order.bag
    bag.pickup_window_start = timezone.now() + timedelta(minutes=45)
    bag.pickup_window_end = timezone.now() + timedelta(hours=2)
    bag.save(update_fields=["pickup_window_start", "pickup_window_end"])

    response = authed.post(
        reverse("v1:business:confirm-pickup-by-scan"),
        {"qr_token": str(paid_order.pickup_qr_token)},
        format="json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_qr_after_15min_late_grace_rejected(authed, paid_order):
    bag = paid_order.bag
    bag.pickup_window_start = timezone.now() - timedelta(hours=3)
    bag.pickup_window_end = timezone.now() - timedelta(minutes=30)
    bag.save(update_fields=["pickup_window_start", "pickup_window_end"])

    response = authed.post(
        reverse("v1:business:confirm-pickup-by-scan"),
        {"qr_token": str(paid_order.pickup_qr_token)},
        format="json",
    )
    assert response.status_code == 409


@pytest.mark.django_db
def test_qr_pending_payment_order_rejected(authed, paid_order):
    paid_order.status = OrderStatus.PENDING_PAYMENT
    paid_order.save(update_fields=["status"])
    response = authed.post(
        reverse("v1:business:confirm-pickup-by-scan"),
        {"qr_token": str(paid_order.pickup_qr_token)},
        format="json",
    )
    assert response.status_code == 409
    assert response.json()["code"] == "pickup_invalid_status"
