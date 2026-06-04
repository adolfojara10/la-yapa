"""/api/v1/consumer/bags/{id}/reviews — paginated reviews list."""

from __future__ import annotations

import pytest
from django.urls import reverse


def url(bag_id) -> str:
    return reverse("v1:consumer:bag-reviews", args=[bag_id])


@pytest.mark.django_db
def test_only_visible_reviews_returned(authed, make_bag):
    from apps.reviews.factories import ReviewFactory

    bag = make_bag()
    visible = ReviewFactory(business_location=bag.business_location, is_visible=True)
    ReviewFactory(business_location=bag.business_location, is_visible=False)

    response = authed.get(url(bag.id))
    ids = [r["id"] for r in response.json()["results"]]
    assert ids == [visible.id]


@pytest.mark.django_db
def test_newest_review_first(authed, make_bag):
    from apps.reviews.factories import ReviewFactory

    bag = make_bag()
    older = ReviewFactory(business_location=bag.business_location)
    newer = ReviewFactory(business_location=bag.business_location)
    response = authed.get(url(bag.id))
    ids = [r["id"] for r in response.json()["results"]]
    assert ids.index(newer.id) < ids.index(older.id)


@pytest.mark.django_db
def test_review_payload_includes_consumer_first_name(authed, make_bag):
    from apps.reviews.factories import ReviewFactory
    from apps.users.factories import ConsumerProfileFactory, UserFactory

    bag = make_bag()
    consumer = UserFactory()
    ConsumerProfileFactory(user=consumer, first_name="Sofía")
    ReviewFactory(
        business_location=bag.business_location,
        consumer=consumer,
        comment="Bolsa increíble.",
        rating=5,
    )
    response = authed.get(url(bag.id))
    payload = response.json()["results"][0]
    assert payload["consumer_first_name"] == "Sofía"
    assert payload["rating"] == 5
    assert payload["comment"] == "Bolsa increíble."
