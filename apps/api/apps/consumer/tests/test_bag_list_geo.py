"""Geo-distance tests — skipped on the SQLite test shim.

These exercise the real PostGIS path (`dwithin`, `Distance` annotation).
CI runs them via the PostGIS service container; local dev with the default
SQLite test settings skips them with a visible SKIP marker.
"""

from __future__ import annotations

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.skipif(
    getattr(settings, "USE_GEO_SHIM", False),
    reason="Requires PostGIS — runs in CI only.",
)

URL = reverse("v1:consumer:bag-list")


@pytest.mark.django_db
def test_distance_filter_within_radius(authed, make_bag):
    from apps.businesses.factories import BusinessLocationFactory
    from apps.geo.utils import make_point

    near_loc = BusinessLocationFactory(location=make_point(-2.9001, -79.0059))
    far_loc = BusinessLocationFactory(location=make_point(-2.7000, -79.0059))  # ~22km
    near_bag = make_bag(location=near_loc)
    make_bag(location=far_loc)

    response = authed.get(URL, {"lat": -2.9001, "lng": -79.0059, "radius_km": 3})
    ids = {b["id"] for b in response.json()["results"]}
    assert str(near_bag.id) in ids
    assert len(ids) == 1


@pytest.mark.django_db
def test_distance_annotation_present_when_location_supplied(authed, make_bag):
    from apps.businesses.factories import BusinessLocationFactory
    from apps.geo.utils import make_point

    loc = BusinessLocationFactory(location=make_point(-2.9001, -79.0059))
    make_bag(location=loc)
    response = authed.get(URL, {"lat": -2.9001, "lng": -79.0059, "radius_km": 5})
    card = response.json()["results"][0]
    assert card["distance_m"] is not None
    assert card["distance_m"] >= 0


@pytest.mark.django_db
def test_distance_sort_orders_nearest_first(authed, make_bag):
    from apps.businesses.factories import BusinessLocationFactory
    from apps.geo.utils import make_point

    near = BusinessLocationFactory(location=make_point(-2.9001, -79.0059))
    far = BusinessLocationFactory(location=make_point(-2.9100, -79.0150))  # ~1.5km
    near_bag = make_bag(location=near)
    far_bag = make_bag(location=far)

    response = authed.get(
        URL,
        {"lat": -2.9001, "lng": -79.0059, "radius_km": 5, "sort": "distance"},
    )
    ids = [b["id"] for b in response.json()["results"]]
    assert ids.index(str(near_bag.id)) < ids.index(str(far_bag.id))


@pytest.mark.django_db
def test_radius_default_is_3km(authed, make_bag):
    """Without an explicit radius_km, default is 3km."""
    from apps.businesses.factories import BusinessLocationFactory
    from apps.geo.utils import make_point

    in_radius = BusinessLocationFactory(location=make_point(-2.9001, -79.0059))
    out_of_radius = BusinessLocationFactory(location=make_point(-2.8000, -79.0059))  # ~11km
    in_bag = make_bag(location=in_radius)
    make_bag(location=out_of_radius)

    response = authed.get(URL, {"lat": -2.9001, "lng": -79.0059})
    ids = {b["id"] for b in response.json()["results"]}
    assert ids == {str(in_bag.id)}
