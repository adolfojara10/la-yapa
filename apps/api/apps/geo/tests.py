"""Geo proxy tests."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from django.core.cache import cache
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.factories import ConsumerProfileFactory, UserFactory


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authed_client(db) -> APIClient:
    client = APIClient()
    user = UserFactory(email="geo@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


@pytest.fixture(autouse=True)
def clear_geo_cache():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "geo-tests",
            }
        }
    ):
        cache.clear()
        yield
        cache.clear()


@pytest.mark.django_db
def test_search_requires_auth(api_client):
    response = api_client.get(reverse("v1:geo:search"), {"q": "cuenca"})
    assert response.status_code == 401


@pytest.mark.django_db
def test_search_normalizes_provider_response(authed_client):
    response_json = {
        "features": [
            {
                "geometry": {"coordinates": [-79.0045, -2.8974]},
                "properties": {
                    "osm_id": 123,
                    "name": "Parque Calderon",
                    "city": "Cuenca",
                    "state": "Azuay",
                    "country": "Ecuador",
                },
            }
        ]
    }
    fake_response = Mock()
    fake_response.json.return_value = response_json
    fake_response.raise_for_status.return_value = None

    with patch("apps.geo.services.requests.get", return_value=fake_response) as get_mock:
        response = authed_client.get(reverse("v1:geo:search"), {"q": "calderon"})

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["results"] == [
        {
            "id": "123",
            "label": "Parque Calderon, Cuenca, Azuay, Ecuador",
            "lat": -2.8974,
            "lng": -79.0045,
        }
    ]
    assert get_mock.call_count == 1


@pytest.mark.django_db
def test_search_uses_cache_for_identical_query(authed_client):
    fake_response = Mock()
    fake_response.json.return_value = {"features": []}
    fake_response.raise_for_status.return_value = None

    with patch("apps.geo.services.requests.get", return_value=fake_response) as get_mock:
        url = reverse("v1:geo:search")
        assert authed_client.get(url, {"q": "cuenca"}).status_code == 200
        assert authed_client.get(url, {"q": "cuenca"}).status_code == 200

    assert get_mock.call_count == 1


@pytest.mark.django_db
def test_reverse_normalizes_first_result(authed_client):
    response_json = {
        "features": [
            {
                "geometry": {"coordinates": [-79.0045, -2.8974]},
                "properties": {
                    "osm_id": 777,
                    "street": "Calle Larga",
                    "housenumber": "4-12",
                    "city": "Cuenca",
                    "country": "Ecuador",
                },
            }
        ]
    }
    fake_response = Mock()
    fake_response.json.return_value = response_json
    fake_response.raise_for_status.return_value = None

    with patch("apps.geo.services.requests.get", return_value=fake_response):
        response = authed_client.get(reverse("v1:geo:reverse"), {"lat": -2.8974, "lng": -79.0045})

    assert response.status_code == 200
    assert response.json()["result"] == {
        "id": "777",
        "label": "Calle Larga 4-12, Cuenca, Ecuador",
        "lat": -2.8974,
        "lng": -79.0045,
    }


@pytest.mark.django_db
def test_provider_failure_returns_502(authed_client):
    from apps.geo.services import GeoProviderError

    with patch("apps.geo.views.search_places", side_effect=GeoProviderError("boom")):
        response = authed_client.get(reverse("v1:geo:search"), {"q": "cuenca"})
    assert response.status_code == 502
