"""Push-token registration endpoint."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications.models import PushToken
from apps.users.factories import UserFactory

URL = reverse("v1:notifications:register-token")


def _authed(user) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


@pytest.mark.django_db
def test_register_token_creates_row():
    user = UserFactory(is_email_verified=True)
    client = _authed(user)
    response = client.post(
        URL,
        {"token": "ExponentPushToken[abc123]", "platform": "android"},
        format="json",
    )
    assert response.status_code == 200
    assert PushToken.objects.filter(user=user, token="ExponentPushToken[abc123]").exists()


@pytest.mark.django_db
def test_register_same_token_twice_is_idempotent():
    user = UserFactory(is_email_verified=True)
    client = _authed(user)
    payload = {"token": "ExponentPushToken[xyz]", "platform": "ios"}
    client.post(URL, payload, format="json")
    client.post(URL, payload, format="json")
    assert PushToken.objects.filter(token="ExponentPushToken[xyz]").count() == 1


@pytest.mark.django_db
def test_register_requires_auth():
    response = APIClient().post(URL, {"token": "x", "platform": "ios"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_token_transfers_to_new_user_on_re_register():
    """If a device is handed off (same Expo token, new user logs in),
    the row's user updates to the latest caller."""
    u1 = UserFactory(email="a@layapa.test", is_email_verified=True)
    u2 = UserFactory(email="b@layapa.test", is_email_verified=True)
    payload = {"token": "ExponentPushToken[device-handoff]", "platform": "android"}
    _authed(u1).post(URL, payload, format="json")
    _authed(u2).post(URL, payload, format="json")
    token = PushToken.objects.get(token="ExponentPushToken[device-handoff]")
    assert token.user == u2
