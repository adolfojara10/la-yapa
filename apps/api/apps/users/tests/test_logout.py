"""POST /api/v1/auth/logout."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.factories import UserFactory

URL = reverse("v1:auth:logout")
REFRESH_URL = reverse("v1:auth:refresh")


@pytest.mark.django_db
def test_logout_blacklists_refresh_token(api_client):
    user = UserFactory()
    refresh = str(RefreshToken.for_user(user))
    response = api_client.post(URL, {"refresh": refresh}, format="json")
    assert response.status_code == 205

    # Using the same refresh after logout must fail.
    again = api_client.post(REFRESH_URL, {"refresh": refresh}, format="json")
    assert again.status_code == 401


@pytest.mark.django_db
def test_logout_is_idempotent_on_already_blacklisted_token(api_client):
    user = UserFactory()
    refresh = str(RefreshToken.for_user(user))
    api_client.post(URL, {"refresh": refresh}, format="json")
    second = api_client.post(URL, {"refresh": refresh}, format="json")
    assert second.status_code == 205


@pytest.mark.django_db
def test_logout_rejects_missing_refresh(api_client):
    response = api_client.post(URL, {}, format="json")
    assert response.status_code == 400
