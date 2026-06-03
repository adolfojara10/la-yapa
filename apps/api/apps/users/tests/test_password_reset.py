"""POST /api/v1/auth/forgot-password and /reset-password."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from apps.users.models import PasswordResetToken

FORGOT_URL = reverse("v1:auth:forgot-password")
RESET_URL = reverse("v1:auth:reset-password")


@pytest.mark.django_db
def test_forgot_password_sends_email_for_known_user(api_client, consumer_user):
    response = api_client.post(FORGOT_URL, {"email": consumer_user.email}, format="json")
    assert response.status_code == 202
    assert PasswordResetToken.objects.filter(user=consumer_user, consumed_at__isnull=True).exists()
    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert "layapa://reset-password?token=" in body
    assert "http://localhost:3000/reset-password?token=" in body


@pytest.mark.django_db
def test_forgot_password_is_silent_for_unknown_email(api_client):
    response = api_client.post(FORGOT_URL, {"email": "ghost@layapa.test"}, format="json")
    assert response.status_code == 202
    assert PasswordResetToken.objects.count() == 0
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_reset_password_happy_path(api_client, consumer_user):
    _, raw = PasswordResetToken.issue(consumer_user)
    response = api_client.post(
        RESET_URL,
        {"token": raw, "new_password": "newpass-strong-99"},
        format="json",
    )
    assert response.status_code == 200
    consumer_user.refresh_from_db()
    assert consumer_user.check_password("newpass-strong-99")


@pytest.mark.django_db
def test_reset_password_rejects_invalid_token(api_client):
    response = api_client.post(
        RESET_URL,
        {"token": "not-a-real-token", "new_password": "newpass-strong-99"},
        format="json",
    )
    assert response.status_code == 400
    assert "token" in response.json()


@pytest.mark.django_db
def test_reset_password_rejects_expired_token(api_client, consumer_user):
    instance, raw = PasswordResetToken.issue(consumer_user)
    instance.expires_at = timezone.now() - timedelta(seconds=1)
    instance.save(update_fields=["expires_at"])
    response = api_client.post(
        RESET_URL,
        {"token": raw, "new_password": "newpass-strong-99"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_reset_password_token_is_single_use(api_client, consumer_user):
    _, raw = PasswordResetToken.issue(consumer_user)
    first = api_client.post(
        RESET_URL,
        {"token": raw, "new_password": "newpass-strong-99"},
        format="json",
    )
    assert first.status_code == 200
    second = api_client.post(
        RESET_URL,
        {"token": raw, "new_password": "different-pass-77"},
        format="json",
    )
    assert second.status_code == 400


@pytest.mark.django_db
def test_reset_password_rejects_weak_password(api_client, consumer_user):
    _, raw = PasswordResetToken.issue(consumer_user)
    response = api_client.post(
        RESET_URL,
        {"token": raw, "new_password": "12345"},
        format="json",
    )
    assert response.status_code == 400
