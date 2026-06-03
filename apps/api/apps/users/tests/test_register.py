"""POST /api/v1/auth/register."""

from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse

from apps.users.models import ConsumerProfile, EmailVerificationCode, User

URL = reverse("v1:auth:register")


@pytest.mark.django_db
def test_register_creates_consumer_with_profile_and_sends_otp(api_client):
    response = api_client.post(
        URL,
        {"email": "alex@layapa.test", "password": "rescuethefood88"},
        format="json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["user"]["email"] == "alex@layapa.test"
    assert body["user"]["role"] == "consumer"
    assert body["user"]["is_email_verified"] is False
    assert body["user"]["onboarding_completed"] is False
    assert "access" in body["tokens"]
    assert "refresh" in body["tokens"]

    user = User.objects.get(email="alex@layapa.test")
    assert ConsumerProfile.objects.filter(user=user).exists()
    assert EmailVerificationCode.objects.filter(user=user, consumed_at__isnull=True).exists()
    assert len(mail.outbox) == 1
    assert "verificación" in mail.outbox[0].subject.lower()


@pytest.mark.django_db
def test_register_normalizes_email_to_lowercase(api_client):
    api_client.post(
        URL,
        {"email": "MIXED@Layapa.TEST", "password": "rescuethefood88"},
        format="json",
    )
    assert User.objects.filter(email="mixed@layapa.test").exists()


@pytest.mark.django_db
def test_register_rejects_duplicate_email(api_client, consumer_user):
    response = api_client.post(
        URL,
        {"email": consumer_user.email, "password": "rescuethefood88"},
        format="json",
    )
    assert response.status_code == 400
    assert "email" in response.json()


@pytest.mark.django_db
def test_register_rejects_weak_password(api_client):
    response = api_client.post(
        URL,
        {"email": "weak@layapa.test", "password": "12345"},
        format="json",
    )
    assert response.status_code == 400
    assert "password" in response.json()


@pytest.mark.django_db
def test_register_can_create_business_owner_without_profile(api_client):
    response = api_client.post(
        URL,
        {
            "email": "biz@layapa.test",
            "password": "rescuethefood88",
            "role": "business_owner",
        },
        format="json",
    )
    assert response.status_code == 201
    user = User.objects.get(email="biz@layapa.test")
    assert user.role == "business_owner"
    # Business owners don't get a ConsumerProfile — Business is created later via onboarding.
    assert not ConsumerProfile.objects.filter(user=user).exists()
    assert response.json()["user"]["onboarding_completed"] is True


@pytest.mark.django_db
def test_register_rejects_disallowed_roles(api_client):
    response = api_client.post(
        URL,
        {
            "email": "evil@layapa.test",
            "password": "rescuethefood88",
            "role": "admin",
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_is_atomic_on_email_failure(api_client, monkeypatch):
    """If the email send blows up, no user should be left in the DB."""

    def boom(*args, **kwargs):
        raise RuntimeError("smtp down")

    from apps.users.auth.services import email_otp

    monkeypatch.setattr(email_otp, "send_templated_email", boom)
    with pytest.raises(RuntimeError):
        api_client.post(
            URL,
            {"email": "atomic@layapa.test", "password": "rescuethefood88"},
            format="json",
        )
    assert not User.objects.filter(email="atomic@layapa.test").exists()
