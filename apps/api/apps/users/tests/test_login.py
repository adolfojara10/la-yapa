"""POST /api/v1/auth/login and /api/v1/auth/refresh."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.users.factories import UserFactory

LOGIN_URL = reverse("v1:auth:login")
REFRESH_URL = reverse("v1:auth:refresh")


@pytest.mark.django_db
def test_login_returns_tokens_and_user(api_client):
    UserFactory(email="login@layapa.test", password="rescuethefood88", is_email_verified=True)
    response = api_client.post(
        LOGIN_URL,
        {"email": "login@layapa.test", "password": "rescuethefood88"},
        format="json",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["user"]["email"] == "login@layapa.test"
    assert "access" in body["tokens"]
    assert "refresh" in body["tokens"]


@pytest.mark.django_db
def test_login_is_case_insensitive_for_email(api_client):
    UserFactory(email="login@layapa.test", password="rescuethefood88")
    response = api_client.post(
        LOGIN_URL,
        {"email": "LOGIN@LAYAPA.TEST", "password": "rescuethefood88"},
        format="json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_rejects_wrong_password(api_client):
    UserFactory(email="login@layapa.test", password="rescuethefood88")
    response = api_client.post(
        LOGIN_URL,
        {"email": "login@layapa.test", "password": "nope-not-it"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_login_rejects_inactive_user(api_client):
    UserFactory(email="dead@layapa.test", password="rescuethefood88", is_active=False)
    response = api_client.post(
        LOGIN_URL,
        {"email": "dead@layapa.test", "password": "rescuethefood88"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_refresh_returns_new_access_token(api_client):
    UserFactory(email="login@layapa.test", password="rescuethefood88")
    login = api_client.post(
        LOGIN_URL,
        {"email": "login@layapa.test", "password": "rescuethefood88"},
        format="json",
    ).json()
    response = api_client.post(REFRESH_URL, {"refresh": login["tokens"]["refresh"]}, format="json")
    assert response.status_code == 200
    assert "access" in response.json()
