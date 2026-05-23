"""Geo field shim.

In production (Postgres + PostGIS) we use real `django.contrib.gis` PointField so
that GIS lookups (`distance_lt`, `dwithin`, …) work natively.

In tests (SQLite), GeoDjango fields would require SpatiaLite which is painful to
install on contributors' machines. We fall back to a JSONField holding
`{"lat": float, "lng": float}` — enough for round-trip storage in unit tests.
Distance queries are not exercised by unit tests; they're covered in CI's
PostGIS-backed integration tests.

Use it as a drop-in:

    from apps.geo.fields import PointField

    location = PointField(null=True, blank=True)
"""

from __future__ import annotations

from django.conf import settings

if getattr(settings, "USE_GEO_SHIM", False):
    # ---------- SQLite test path ----------
    from django.db import models

    class PointField(models.JSONField):
        """JSON-backed lat/lng placeholder used in tests."""

        description = "Lat/lng point (JSON shim for tests)"

        def __init__(self, *args, srid=4326, geography=False, **kwargs):
            # Swallow PostGIS-only kwargs so model code is identical.
            self._srid = srid
            self._geography = geography
            kwargs.setdefault("null", True)
            kwargs.setdefault("blank", True)
            super().__init__(*args, **kwargs)

        def deconstruct(self):
            name, path, args, kwargs = super().deconstruct()
            # Don't surface the swallowed kwargs in migrations.
            return name, path, args, kwargs

else:
    # ---------- Real PostGIS path ----------
    from django.contrib.gis.db.models import PointField as _PostGISPointField

    class PointField(_PostGISPointField):  # type: ignore[no-redef,misc]
        """Standard GeoDjango PointField with SRID 4326 (WGS84) by default."""

        def __init__(self, *args, srid=4326, **kwargs):
            super().__init__(*args, srid=srid, **kwargs)
