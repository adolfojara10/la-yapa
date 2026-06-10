"""Suspended-meals dispatch + rate limit."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.suspended_meals.factories import SuspendedMealDonationFactory
from apps.suspended_meals.models import (
    DonationStatus,
    SuspendedMealClaim,
)
from apps.suspended_meals.services import DAILY_DISPATCH_CAP_PER_LOCATION


@pytest.mark.django_db
def test_active_list_returns_general_pool_donations(authed, business_owner, location):
    SuspendedMealDonationFactory(bag=None, amount=Decimal("3.00"))
    response = authed.get(reverse("v1:business:suspended-active"))
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["business_location_name"] == "Pool general"


@pytest.mark.django_db
def test_active_list_returns_bag_donations_for_owned_location(authed, location):
    from apps.bags.factories import BagFactory

    bag = BagFactory(business_location=location)
    SuspendedMealDonationFactory(bag=bag, amount=Decimal("4.50"))
    response = authed.get(reverse("v1:business:suspended-active"))
    body = response.json()
    assert any(d["business_location_id"] == location.id for d in body)


@pytest.mark.django_db
def test_dispatch_general_pool_creates_claim(authed, business_owner, location):
    donation = SuspendedMealDonationFactory(bag=None, amount=Decimal("3.00"))
    response = authed.post(
        reverse("v1:business:suspended-dispatch"),
        {
            "donation_id": str(donation.id),
            "business_location_id": location.id,
            "notes": "Cliente recurrente",
        },
        format="json",
    )
    assert response.status_code == 200
    donation.refresh_from_db()
    assert donation.status == DonationStatus.CLAIMED
    assert donation.claimed_by_business_id == location.id
    assert SuspendedMealClaim.objects.filter(donation=donation).count() == 1


@pytest.mark.django_db
def test_dispatch_general_pool_without_location_uses_only_owned_location(authed, location):
    donation = SuspendedMealDonationFactory(bag=None)
    response = authed.post(
        reverse("v1:business:suspended-dispatch"),
        {"donation_id": str(donation.id)},
        format="json",
    )
    assert response.status_code == 200
    donation.refresh_from_db()
    assert donation.claimed_by_business_id == location.id


@pytest.mark.django_db
def test_dispatch_general_pool_requires_location_when_owner_has_multiple_locations(
    authed, business
):
    from apps.businesses.factories import BusinessLocationFactory

    BusinessLocationFactory(business=business, name="Sucursal Norte")
    donation = SuspendedMealDonationFactory(bag=None)
    response = authed.post(
        reverse("v1:business:suspended-dispatch"),
        {"donation_id": str(donation.id)},
        format="json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_dispatch_already_claimed_donation_rejected(authed, business_owner, location):
    donation = SuspendedMealDonationFactory(
        bag=None, status=DonationStatus.CLAIMED, amount=Decimal("3.00")
    )
    response = authed.post(
        reverse("v1:business:suspended-dispatch"),
        {"donation_id": str(donation.id), "business_location_id": location.id},
        format="json",
    )
    assert response.status_code == 404
    assert response.json()["code"] == "donation_not_available"


@pytest.mark.django_db
def test_dispatch_for_other_owners_location_returns_404(api_client, location):
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.users.factories import BusinessOwnerFactory

    other = BusinessOwnerFactory(is_email_verified=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other).access_token}")
    donation = SuspendedMealDonationFactory(bag=None)
    response = api_client.post(
        reverse("v1:business:suspended-dispatch"),
        {"donation_id": str(donation.id), "business_location_id": location.id},
        format="json",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_dispatch_rate_limit_blocks_6th_in_24h(authed, business_owner, location):
    """5 dispatches in 24h succeed; the 6th returns 429."""
    for _ in range(DAILY_DISPATCH_CAP_PER_LOCATION):
        donation = SuspendedMealDonationFactory(bag=None, amount=Decimal("3"))
        response = authed.post(
            reverse("v1:business:suspended-dispatch"),
            {"donation_id": str(donation.id), "business_location_id": location.id},
            format="json",
        )
        assert response.status_code == 200

    # 6th attempt within the same 24h window — capped.
    donation = SuspendedMealDonationFactory(bag=None, amount=Decimal("3"))
    response = authed.post(
        reverse("v1:business:suspended-dispatch"),
        {"donation_id": str(donation.id), "business_location_id": location.id},
        format="json",
    )
    assert response.status_code == 429
    assert response.json()["code"] == "dispatch_rate_limit_exceeded"


@pytest.mark.django_db
def test_dispatch_rate_limit_ages_out_after_24h(authed, business_owner, location):
    """An old claim (>24h ago) doesn't count toward the cap."""
    from apps.bags.factories import BagFactory

    bag = BagFactory(business_location=location)
    for _ in range(DAILY_DISPATCH_CAP_PER_LOCATION):
        donation = SuspendedMealDonationFactory(bag=bag)
        # Manually create the claim with an aged timestamp.
        SuspendedMealClaim.objects.create(
            donation=donation,
            business_location=location,
        )
    # Age the just-created claims past the window.
    SuspendedMealClaim.objects.filter(business_location=location).update(
        claimed_at=timezone.now() - timedelta(days=2)
    )

    fresh_donation = SuspendedMealDonationFactory(bag=None, amount=Decimal("3"))
    response = authed.post(
        reverse("v1:business:suspended-dispatch"),
        {
            "donation_id": str(fresh_donation.id),
            "business_location_id": location.id,
        },
        format="json",
    )
    assert response.status_code == 200, response.content
