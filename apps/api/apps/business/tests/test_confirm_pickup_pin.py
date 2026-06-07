"""Pickup confirmation via PIN entry + brute-force lockout."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.orders.models import Order, OrderStatus
from apps.orders.services import register_pin_miss


@pytest.mark.django_db
def test_pin_happy_path_completes_order(authed, paid_order):
    response = authed.post(
        reverse("v1:business:confirm-pickup-by-pin"),
        {
            "business_location_id": paid_order.business_location_id,
            "pin": paid_order.pickup_code,
        },
        format="json",
    )
    assert response.status_code == 200
    paid_order.refresh_from_db()
    assert paid_order.status == OrderStatus.COMPLETED


@pytest.mark.django_db
def test_register_pin_miss_bumps_counter_when_pin_matches_existing_order(
    business_owner, paid_order
):
    """Direct service-level test — easier than going through HTTP because
    `confirm_pickup_by_pin` would COMPLETE the order on a correct PIN
    match (no miss to register)."""
    paid_order.pickup_code = "1234"
    paid_order.save(update_fields=["pickup_code"])

    register_pin_miss(
        business_owner=business_owner,
        business_location_id=paid_order.business_location_id,
        pin="1234",
    )

    paid_order.refresh_from_db()
    assert paid_order.pin_attempts == 1


@pytest.mark.django_db
def test_register_pin_miss_no_op_for_non_matching_pin(business_owner, paid_order):
    """A guess against a non-existent (location, pin) combo bumps nothing."""
    initial_attempts = paid_order.pin_attempts
    # paid_order has a random pickup_code; pick a definitely-different one.
    bad = "0000" if paid_order.pickup_code != "0000" else "9999"
    register_pin_miss(
        business_owner=business_owner,
        business_location_id=paid_order.business_location_id,
        pin=bad,
    )
    paid_order.refresh_from_db()
    assert paid_order.pin_attempts == initial_attempts


@pytest.mark.django_db
def test_register_pin_miss_no_op_for_other_owners_location(
    paid_order,
):
    """A different owner cannot remotely bump another order's counter
    (sealed at the service boundary, not just the view)."""
    from apps.users.factories import BusinessOwnerFactory

    other_owner = BusinessOwnerFactory(is_email_verified=True)
    paid_order.pickup_code = "1234"
    paid_order.save(update_fields=["pickup_code"])

    register_pin_miss(
        business_owner=other_owner,
        business_location_id=paid_order.business_location_id,
        pin="1234",
    )
    paid_order.refresh_from_db()
    assert paid_order.pin_attempts == 0


@pytest.mark.django_db
def test_lockout_at_5_attempts_blocks_correct_pin(authed, paid_order, business_owner):
    """Drive register_pin_miss 5x at the service layer (each call bumps),
    then attempt confirm via HTTP with the correct PIN → 423 Locked."""
    paid_order.pickup_code = "1234"
    paid_order.save(update_fields=["pickup_code"])

    for _ in range(Order.PIN_MAX_ATTEMPTS):
        register_pin_miss(
            business_owner=business_owner,
            business_location_id=paid_order.business_location_id,
            pin="1234",
        )

    paid_order.refresh_from_db()
    assert paid_order.pin_attempts >= Order.PIN_MAX_ATTEMPTS
    assert paid_order.pin_locked_at is not None

    # The correct PIN now returns 423 Locked.
    response = authed.post(
        reverse("v1:business:confirm-pickup-by-pin"),
        {
            "business_location_id": paid_order.business_location_id,
            "pin": "1234",
        },
        format="json",
    )
    assert response.status_code == 423
    assert response.json()["code"] == "pin_locked"


@pytest.mark.django_db
def test_qr_still_works_after_pin_lockout(authed, paid_order):
    """QR is the unlocked bypass path even when PIN is fully locked."""
    paid_order.pin_attempts = Order.PIN_MAX_ATTEMPTS
    paid_order.pin_locked_at = timezone.now()
    paid_order.save(update_fields=["pin_attempts", "pin_locked_at"])

    response = authed.post(
        reverse("v1:business:confirm-pickup-by-scan"),
        {"qr_token": str(paid_order.pickup_qr_token)},
        format="json",
    )
    assert response.status_code == 200
    paid_order.refresh_from_db()
    assert paid_order.status == OrderStatus.COMPLETED


@pytest.mark.django_db
def test_pin_for_other_owners_location_returns_404_no_counter_bump(api_client, paid_order):
    """Cross-business attempts return 404 AND don't bump the target's
    counter (would otherwise be a remote-lock DoS)."""
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.users.factories import BusinessOwnerFactory

    other = BusinessOwnerFactory(is_email_verified=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other).access_token}")
    paid_order.pickup_code = "1234"
    paid_order.save(update_fields=["pickup_code"])

    response = api_client.post(
        reverse("v1:business:confirm-pickup-by-pin"),
        {
            "business_location_id": paid_order.business_location_id,
            "pin": "1234",
        },
        format="json",
    )
    assert response.status_code == 404
    paid_order.refresh_from_db()
    assert paid_order.pin_attempts == 0


@pytest.mark.django_db
def test_pin_outside_window_does_not_charge_attempt(authed, paid_order):
    """Window failure is timing, not a wrong PIN — don't bump the counter."""
    bag = paid_order.bag
    bag.pickup_window_start = timezone.now() + timedelta(hours=4)
    bag.pickup_window_end = timezone.now() + timedelta(hours=6)
    bag.save(update_fields=["pickup_window_start", "pickup_window_end"])

    response = authed.post(
        reverse("v1:business:confirm-pickup-by-pin"),
        {
            "business_location_id": paid_order.business_location_id,
            "pin": paid_order.pickup_code,
        },
        format="json",
    )
    assert response.status_code == 409
    paid_order.refresh_from_db()
    assert paid_order.pin_attempts == 0


@pytest.mark.django_db
def test_confirm_pickup_by_id_with_pin(authed, paid_order):
    """The /orders/{id}/confirm-pickup endpoint also accepts PIN."""
    response = authed.post(
        reverse("v1:business:confirm-pickup-by-id", args=[paid_order.id]),
        {"pin": paid_order.pickup_code},
        format="json",
    )
    assert response.status_code == 200
    paid_order.refresh_from_db()
    assert paid_order.status == OrderStatus.COMPLETED


@pytest.mark.django_db
def test_confirm_pickup_by_id_rejects_both_qr_and_pin(authed, paid_order):
    response = authed.post(
        reverse("v1:business:confirm-pickup-by-id", args=[paid_order.id]),
        {
            "qr_token": str(paid_order.pickup_qr_token),
            "pin": paid_order.pickup_code,
        },
        format="json",
    )
    assert response.status_code == 400
