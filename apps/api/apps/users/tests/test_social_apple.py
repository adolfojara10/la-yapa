"""POST /api/v1/auth/apple — identity-token verification fully mocked.

We mock jwt.decode + jwt.get_unverified_header to avoid pulling real JWKS keys
or generating an RSA keypair just to test the view layer.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from apps.users.factories import UserFactory
from apps.users.models import User

URL = reverse("v1:auth:apple")


def _claims(**overrides):
    base = {
        "iss": "https://appleid.apple.com",
        "aud": "ec.layapa.app.test",
        "sub": "apple-uid-1",
        "email": "appleuser@privaterelay.appleid.com",
        "email_verified": True,
        "exp": 9_999_999_999,
        "iat": 1,
    }
    base.update(overrides)
    return base


def _patches(claims):
    """Stack of patches that bypass real Apple JWKS / signature verification."""
    fake_jwk = MagicMock()
    fake_jwk.key = "fake-rsa-key"
    return (
        patch(
            "apps.users.auth.services.apple.jwt.get_unverified_header",
            return_value={"kid": "fake-kid", "alg": "RS256"},
        ),
        patch(
            "apps.users.auth.services.apple._fetch_jwks",
            return_value={"keys": [{"kid": "fake-kid", "kty": "RSA", "n": "x", "e": "AQAB"}]},
        ),
        patch("apps.users.auth.services.apple.jwt.PyJWK", return_value=fake_jwk),
        patch("apps.users.auth.services.apple.jwt.decode", return_value=claims),
    )


@pytest.mark.django_db
def test_apple_creates_new_user_on_first_signin(api_client):
    p1, p2, p3, p4 = _patches(_claims())
    with p1, p2, p3, p4:
        response = api_client.post(
            URL, {"identity_token": "fake", "first_name": "Maya"}, format="json"
        )
    assert response.status_code == 200, response.content
    assert response.json()["user"]["email"] == "appleuser@privaterelay.appleid.com"

    from allauth.socialaccount.models import SocialAccount

    assert SocialAccount.objects.filter(provider="apple", uid="apple-uid-1").exists()


@pytest.mark.django_db
def test_apple_returns_existing_user_when_sub_known_even_without_email(api_client):
    """Apple omits `email` on subsequent sign-ins; we must look up by sub."""
    from allauth.socialaccount.models import SocialAccount

    existing = UserFactory(email="returningapple@layapa.test", is_email_verified=True)
    SocialAccount.objects.create(provider="apple", uid="apple-uid-1", user=existing)

    claims = _claims(email="")
    p1, p2, p3, p4 = _patches(claims)
    with p1, p2, p3, p4:
        response = api_client.post(URL, {"identity_token": "fake"}, format="json")
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "returningapple@layapa.test"
    assert User.objects.filter(email="returningapple@layapa.test").count() == 1


@pytest.mark.django_db
def test_apple_rejects_no_email_and_unknown_sub(api_client):
    claims = _claims(email="", sub="unknown-sub")
    p1, p2, p3, p4 = _patches(claims)
    with p1, p2, p3, p4:
        response = api_client.post(URL, {"identity_token": "fake"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_apple_rejects_invalid_token(api_client):
    import jwt

    with patch(
        "apps.users.auth.services.apple.jwt.get_unverified_header",
        side_effect=jwt.PyJWTError("bad"),
    ):
        response = api_client.post(URL, {"identity_token": "fake"}, format="json")
    assert response.status_code == 400
