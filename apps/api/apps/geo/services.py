"""Geo provider client + response normalization for search/reverse geocoding."""

from __future__ import annotations

import hashlib
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

ECUADOR_BBOX = "-81.1,-5.2,-75.0,1.9"


class GeoProviderError(Exception):
    """Raised when the configured geo provider is unavailable or returns bad data."""


def search_places(
    *,
    query: str,
    country: str = "ec",
    limit: int = 5,
    lat: float | None = None,
    lng: float | None = None,
    lang: str | None = None,
) -> list[dict[str, Any]]:
    cache_key = _cache_key(
        "search",
        query=query,
        country=country,
        limit=limit,
        lat=lat,
        lng=lng,
        lang=lang,
    )
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params: dict[str, Any] = {"q": query, "limit": limit}
    if lang:
        params["lang"] = lang
    if lat is not None and lng is not None:
        params["lat"] = lat
        params["lon"] = lng
    if country.lower() == "ec":
        params["bbox"] = ECUADOR_BBOX

    body = _provider_get(settings.GEO_PROVIDER_SEARCH_URL, params=params)
    results = [_normalize_feature(feature) for feature in body.get("features", [])]
    cache.set(cache_key, results, timeout=settings.GEO_SEARCH_CACHE_TTL_SECONDS)
    return results


def reverse_geocode(*, lat: float, lng: float, lang: str | None = None) -> dict[str, Any] | None:
    cache_key = _cache_key("reverse", lat=lat, lng=lng, lang=lang)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params: dict[str, Any] = {"lat": lat, "lon": lng}
    if lang:
        params["lang"] = lang

    body = _provider_get(settings.GEO_PROVIDER_REVERSE_URL, params=params)
    features = body.get("features", [])
    result = _normalize_feature(features[0]) if features else None
    cache.set(cache_key, result, timeout=settings.GEO_REVERSE_CACHE_TTL_SECONDS)
    return result


def _provider_get(url: str, *, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": settings.GEO_PROVIDER_USER_AGENT},
            timeout=settings.GEO_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        body = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise GeoProviderError("provider_unavailable") from exc
    if not isinstance(body, dict):
        raise GeoProviderError("invalid_provider_response")
    return body


def _normalize_feature(feature: dict[str, Any]) -> dict[str, Any]:
    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates") or [None, None]
    props = feature.get("properties") or {}
    lng = coords[0] if len(coords) > 0 else None
    lat = coords[1] if len(coords) > 1 else None
    return {
        "id": str(props.get("osm_id") or props.get("osm_key") or f"{lat},{lng}"),
        "label": _build_label(props),
        "lat": lat,
        "lng": lng,
    }


def _build_label(props: dict[str, Any]) -> str:
    street_line = _street_line(props)
    primary = props.get("name") or street_line or props.get("city") or "Ubicacion"
    parts = [
        primary,
        street_line if street_line != primary else "",
        props.get("district"),
        props.get("city"),
        props.get("state"),
        props.get("country"),
    ]
    seen: list[str] = []
    for raw in parts:
        value = str(raw).strip() if raw else ""
        if value and value not in seen:
            seen.append(value)
    return ", ".join(seen)


def _street_line(props: dict[str, Any]) -> str:
    street = str(props.get("street") or "").strip()
    number = str(props.get("housenumber") or "").strip()
    if street and number:
        return f"{street} {number}"
    return street or number


def _cache_key(prefix: str, **parts: Any) -> str:
    material = "|".join(f"{key}={parts[key]}" for key in sorted(parts))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return f"geo:{prefix}:{digest}"
