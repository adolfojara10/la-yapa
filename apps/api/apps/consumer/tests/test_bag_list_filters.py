"""Filter behavior for /api/v1/consumer/bags (no geo)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

URL = reverse("v1:consumer:bag-list")


@pytest.mark.django_db
def test_requires_auth(api_client):
    response = api_client.get(URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_business_owner_role_rejected(api_client):
    """Only consumers can hit consumer endpoints."""
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.users.factories import BusinessOwnerFactory

    biz = BusinessOwnerFactory(is_email_verified=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(biz).access_token}")
    response = api_client.get(URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_unverified_consumer_rejected(api_client):
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.users.factories import ConsumerProfileFactory, UserFactory

    user = UserFactory(is_email_verified=False)
    ConsumerProfileFactory(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    response = api_client.get(URL)
    assert response.status_code == 403


@pytest.mark.django_db
def test_excludes_inactive_bags(authed, make_bag):
    make_bag(is_active=True)
    make_bag(is_active=False)
    response = authed.get(URL)
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1


@pytest.mark.django_db
def test_excludes_expired_bags(authed, make_bag):
    fresh = make_bag()
    expired = make_bag()
    expired.pickup_window_start = timezone.now() - timedelta(hours=4)
    expired.pickup_window_end = timezone.now() - timedelta(hours=2)
    expired.save()
    response = authed.get(URL)
    ids = [b["id"] for b in response.json()["results"]]
    assert str(fresh.id) in ids
    assert str(expired.id) not in ids


@pytest.mark.django_db
def test_dietary_filter_uses_AND_semantics(authed, make_bag, vegan_tag, gluten_free_tag):
    vegan_only = make_bag(dietary=[vegan_tag])
    both = make_bag(dietary=[vegan_tag, gluten_free_tag])
    make_bag(dietary=[gluten_free_tag])
    response = authed.get(URL, {"dietary": "vegan,gluten_free"})
    ids = {b["id"] for b in response.json()["results"]}
    assert ids == {str(both.id)}
    assert str(vegan_only.id) not in ids


@pytest.mark.django_db
def test_allergen_exclusion(authed, make_bag, gluten_allergen, mani_allergen):
    clean = make_bag()
    has_gluten = make_bag(allergens=[gluten_allergen])
    has_mani = make_bag(allergens=[mani_allergen])
    response = authed.get(URL, {"exclude_allergens": "gluten,mani"})
    ids = {b["id"] for b in response.json()["results"]}
    assert str(clean.id) in ids
    assert str(has_gluten.id) not in ids
    assert str(has_mani.id) not in ids


@pytest.mark.django_db
def test_price_range_bounds(authed, make_bag):
    cheap = make_bag(sale_price="2.00", original_price="10.00")
    mid = make_bag(sale_price="4.50", original_price="12.00")
    pricey = make_bag(sale_price="7.00", original_price="20.00")
    response = authed.get(URL, {"min_price": "3.00", "max_price": "5.00"})
    ids = {b["id"] for b in response.json()["results"]}
    assert ids == {str(mid.id)}
    assert str(cheap.id) not in ids and str(pricey.id) not in ids


@pytest.mark.django_db
def test_pickup_window_today_excludes_tomorrow(authed, make_bag):
    later_today = make_bag(hours_ahead=3)
    tomorrow = make_bag(hours_ahead=30)
    response = authed.get(URL, {"pickup_window": "today"})
    ids = {b["id"] for b in response.json()["results"]}
    assert str(later_today.id) in ids
    assert str(tomorrow.id) not in ids


@pytest.mark.django_db
def test_text_search_matches_title_and_business_name(authed, make_bag, panaderia_location):
    bread = make_bag(location=panaderia_location, title="Pan integral del día")
    other = make_bag(title="Bolsa sorpresa #99")
    # Query matches the business name on the first bag, not the second.
    response = authed.get(URL, {"q": "esperanza"})
    ids = {b["id"] for b in response.json()["results"]}
    assert str(bread.id) in ids
    assert str(other.id) not in ids


@pytest.mark.django_db
def test_min_rating_filter(authed, make_bag, consumer):
    from apps.reviews.factories import ReviewFactory

    well_rated = make_bag()
    poorly_rated = make_bag()
    # 3 five-star reviews for `well_rated`'s location.
    for _ in range(3):
        ReviewFactory(
            business_location=well_rated.business_location,
            rating=5,
        )
    # 2 two-star reviews for `poorly_rated`'s location.
    for _ in range(2):
        ReviewFactory(
            business_location=poorly_rated.business_location,
            rating=2,
        )
    response = authed.get(URL, {"min_rating": "4.0"})
    ids = {b["id"] for b in response.json()["results"]}
    assert str(well_rated.id) in ids
    assert str(poorly_rated.id) not in ids


@pytest.mark.django_db
def test_sort_price_orders_cheapest_first(authed, make_bag):
    a = make_bag(sale_price="4.50", original_price="12.00")
    b = make_bag(sale_price="2.50", original_price="10.00")
    c = make_bag(sale_price="6.00", original_price="20.00")
    response = authed.get(URL, {"sort": "price"})
    ids_in_order = [b_["id"] for b_ in response.json()["results"]]
    # Cheapest first.
    assert ids_in_order.index(str(b.id)) < ids_in_order.index(str(a.id))
    assert ids_in_order.index(str(a.id)) < ids_in_order.index(str(c.id))


@pytest.mark.django_db
def test_distance_sort_silently_degrades_to_ending_soon_without_location(authed, make_bag):
    """When `sort=distance` but no lat/lng (and no default_location), the
    server falls back to ending_soon instead of returning 400."""
    soon = make_bag(hours_ahead=2)
    later = make_bag(hours_ahead=10)
    response = authed.get(URL, {"sort": "distance"})
    assert response.status_code == 200
    ids_in_order = [b["id"] for b in response.json()["results"]]
    assert ids_in_order.index(str(soon.id)) < ids_in_order.index(str(later.id))


@pytest.mark.django_db
def test_card_payload_includes_required_fields(authed, make_bag, vegan_tag):
    bag = make_bag(
        dietary=[vegan_tag],
        sale_price="3.00",
        original_price="10.00",
    )
    response = authed.get(URL)
    card = response.json()["results"][0]
    assert card["id"] == str(bag.id)
    assert card["discount_percent"] == 70
    assert Decimal(card["sale_price"]) == Decimal("3.00")
    assert card["is_favorited"] is False  # never favorited yet
    assert card["dietary_tags"] == ["vegan"]
    assert card["business"]["name"] == bag.business_location.business.name
    assert card["business"]["rating_count"] == 0
