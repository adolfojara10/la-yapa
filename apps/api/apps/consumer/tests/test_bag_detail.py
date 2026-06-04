"""/api/v1/consumer/bags/{id} — detail endpoint."""

from __future__ import annotations

import uuid

import pytest
from django.urls import reverse


def url(bag_id) -> str:
    return reverse("v1:consumer:bag-detail", args=[bag_id])


@pytest.mark.django_db
def test_returns_full_detail_payload(authed, make_bag, vegan_tag):
    bag = make_bag(dietary=[vegan_tag])
    bag.description = "Pan, queso, frutas"
    bag.extra_image_urls = ["https://images.unsplash.com/a", "https://images.unsplash.com/b"]
    bag.save()

    response = authed.get(url(bag.id))
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(bag.id)
    assert body["description"] == "Pan, queso, frutas"
    assert len(body["extra_image_urls"]) == 2
    assert body["business_hours"] == {}
    assert body["is_active"] is True
    assert body["quantity_total"] == bag.quantity_total
    assert body["latest_reviews"] == []


@pytest.mark.django_db
def test_404_for_unknown_id(authed):
    response = authed.get(url(uuid.uuid4()))
    assert response.status_code == 404


@pytest.mark.django_db
def test_inactive_bag_still_readable_with_flag(authed, make_bag):
    bag = make_bag(is_active=False)
    response = authed.get(url(bag.id))
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.django_db
def test_latest_reviews_capped_at_three(authed, make_bag):
    from apps.reviews.factories import ReviewFactory

    bag = make_bag()
    for _ in range(5):
        ReviewFactory(business_location=bag.business_location, rating=4)
    response = authed.get(url(bag.id))
    assert len(response.json()["latest_reviews"]) == 3
