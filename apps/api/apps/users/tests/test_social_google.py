"""POST /api/v1/auth/google — id_token verification fully mocked."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.users.factories import UserFactory
from apps.users.models import User

URL = reverse("v1:auth:google")


def _claims(**overrides):
    base = {
        "iss": "https://accounts.google.com",
        "aud": "test-google-client-id.apps.googleusercontent.com",
        "sub": "google-uid-1",
        "email": "newgoogleuser@layapa.test",
        "email_verified": True,
        "given_name": "Maya",
        "family_name": "Rivera",
        "picture": "https://example.com/pic.png",
    }
    base.update(overrides)
    return base


@pytest.mark.django_db
def test_google_creates_new_user_when_unknown_email(api_client):
    with patch(
        "apps.users.auth.services.google.google_id_token.verify_oauth2_token",
        return_value=_claims(),
    ):
        response = api_client.post(URL, {"id_token": "fake-token"}, format="json")
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["user"]["email"] == "newgoogleuser@layapa.test"
    assert body["user"]["is_email_verified"] is True
    assert "access" in body["tokens"]

    from allauth.socialaccount.models import SocialAccount

    user = User.objects.get(email="newgoogleuser@layapa.test")
    assert SocialAccount.objects.filter(provider="google", uid="google-uid-1", user=user).exists()


@pytest.mark.django_db
def test_google_links_to_existing_user_by_email(api_client):
    user = UserFactory(email="newgoogleuser@layapa.test", is_email_verified=False)
    with patch(
        "apps.users.auth.services.google.google_id_token.verify_oauth2_token",
        return_value=_claims(),
    ):
        response = api_client.post(URL, {"id_token": "fake-token"}, format="json")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_email_verified is True
    assert User.objects.filter(email="newgoogleuser@layapa.test").count() == 1


@pytest.mark.django_db
def test_google_rejects_wrong_audience(api_client):
    with patch(
        "apps.users.auth.services.google.google_id_token.verify_oauth2_token",
        return_value=_claims(aud="some-other-app.apps.googleusercontent.com"),
    ):
        response = api_client.post(URL, {"id_token": "fake-token"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_google_rejects_unverified_email(api_client):
    with patch(
        "apps.users.auth.services.google.google_id_token.verify_oauth2_token",
        return_value=_claims(email_verified=False),
    ):
        response = api_client.post(URL, {"id_token": "fake-token"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_google_rejects_invalid_token_signature(api_client):
    with patch(
        "apps.users.auth.services.google.google_id_token.verify_oauth2_token",
        side_effect=ValueError("Wrong signature"),
    ):
        response = api_client.post(URL, {"id_token": "fake-token"}, format="json")
    assert response.status_code == 400
