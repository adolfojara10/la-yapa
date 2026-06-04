"""POST /api/v1/consumer/business-locations/{id}/favorite — toggle."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.businesses.models import Favorite


def url(location_id: int) -> str:
    return reverse("v1:consumer:favorite-toggle", args=[location_id])


@pytest.mark.django_db
def test_first_call_creates_favorite(authed, make_bag, consumer):
    bag = make_bag()
    response = authed.post(url(bag.business_location_id))
    assert response.status_code == 200
    body = response.json()
    assert body == {"favorited": True, "business_location_id": bag.business_location_id}
    assert Favorite.objects.filter(
        user=consumer, business_location_id=bag.business_location_id
    ).exists()


@pytest.mark.django_db
def test_second_call_removes_favorite(authed, make_bag, consumer):
    bag = make_bag()
    authed.post(url(bag.business_location_id))
    response = authed.post(url(bag.business_location_id))
    assert response.json()["favorited"] is False
    assert not Favorite.objects.filter(
        user=consumer, business_location_id=bag.business_location_id
    ).exists()


@pytest.mark.django_db
def test_404_on_unknown_location(authed):
    response = authed.post(url(999_999))
    assert response.status_code == 404


@pytest.mark.django_db
def test_card_is_favorited_flag_reflects_state(authed, make_bag):
    """The list endpoint's `is_favorited` annotation must update after a toggle."""
    bag = make_bag()
    list_url = reverse("v1:consumer:bag-list")

    initial = authed.get(list_url).json()["results"][0]
    assert initial["is_favorited"] is False

    authed.post(url(bag.business_location_id))
    after = authed.get(list_url).json()["results"][0]
    assert after["is_favorited"] is True
