"""Geo helpers — building Points from lat/lng tuples (works in both backends)."""

from __future__ import annotations

from typing import Any

from django.conf import settings


def make_point(lat: float, lng: float) -> Any:
    """Return a value suitable for assigning to a `geo.fields.PointField`.

    In PostGIS mode → a `django.contrib.gis.geos.Point`.
    In test/shim mode → a `{"lat": float, "lng": float}` dict.
    """
    if getattr(settings, "USE_GEO_SHIM", False):
        return {"lat": float(lat), "lng": float(lng)}
    from django.contrib.gis.geos import Point

    return Point(float(lng), float(lat), srid=4326)
