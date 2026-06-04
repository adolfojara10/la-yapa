"""Geo helpers for the bag list.

Two distinct backends behind `apps.geo.fields.PointField`:
  - PostGIS in dev/prod (real Point geometry)
  - JSON shim in tests (no SpatiaLite — see AGENTS.md §5)

This module isolates GeoDjango imports inside functions so importing
`apps.consumer.geo` doesn't blow up when `django.contrib.gis` is excluded
from INSTALLED_APPS (the test settings do this).

Distance is returned in metres. Callers that want km divide by 1000.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db.models import QuerySet


def using_geo_shim() -> bool:
    return bool(getattr(settings, "USE_GEO_SHIM", False))


def annotate_distance(qs: QuerySet, lat: float, lng: float) -> QuerySet:
    """Annotate `distance_m` on each Bag, measured to (lat, lng) in metres.

    No-op under the test shim — annotations against a JSONField for distance
    would require raw SQL and add no test value. Tests that exercise
    distance ordering / filtering are gated by `@pytest.mark.skipif(USE_GEO_SHIM)`.
    """
    if using_geo_shim():
        return qs
    from django.contrib.gis.db.models.functions import Distance
    from django.contrib.gis.geos import Point

    user_point = Point(float(lng), float(lat), srid=4326)
    return qs.annotate(
        distance_m=Distance("business_location__location", user_point),
    )


def filter_within_radius(qs: QuerySet, lat: float, lng: float, *, radius_km: float) -> QuerySet:
    """Restrict `qs` to bags whose location is within `radius_km` of (lat, lng)."""
    if using_geo_shim():
        return qs
    from django.contrib.gis.db.models.functions import Distance  # noqa: F401 — kept for parity
    from django.contrib.gis.geos import Point
    from django.contrib.gis.measure import D

    user_point = Point(float(lng), float(lat), srid=4326)
    return qs.filter(
        business_location__location__distance_lte=(user_point, D(km=radius_km)),
    )


def resolve_caller_location(
    request_lat: Any, request_lng: Any, user: Any
) -> tuple[float, float] | None:
    """Pick the user-location to use for distance queries.

    Precedence: explicit `?lat=&lng=` params → ConsumerProfile.default_location
    → None (graceful degrade — view falls back to ending_soon sort).
    """
    try:
        if request_lat not in (None, "") and request_lng not in (None, ""):
            return float(request_lat), float(request_lng)
    except (TypeError, ValueError):
        pass

    profile = getattr(user, "consumer_profile", None)
    loc = getattr(profile, "default_location", None) if profile is not None else None
    if loc is None:
        return None
    # PostGIS Point vs. JSON shim dict.
    if hasattr(loc, "y"):
        return float(loc.y), float(loc.x)
    if isinstance(loc, dict):
        lat, lng = loc.get("lat"), loc.get("lng")
        if lat is not None and lng is not None:
            return float(lat), float(lng)
    return None
