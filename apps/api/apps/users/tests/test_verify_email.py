"""POST /api/v1/auth/verify-email and /verify-email/resend."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from apps.users.factories import UserFactory
from apps.users.models import EmailVerificationCode

VERIFY_URL = reverse("v1:auth:verify-email")
RESEND_URL = reverse("v1:auth:verify-email-resend")


@pytest.fixture
def user_with_code(db):
    user = UserFactory(email="verify@layapa.test", is_email_verified=False)
    code = EmailVerificationCode.issue(user)
    return user, code


@pytest.mark.django_db
def test_verify_happy_path(api_client, user_with_code):
    user, code = user_with_code
    response = api_client.post(VERIFY_URL, {"email": user.email, "code": code.code}, format="json")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_email_verified is True
    assert user.email_verified_at is not None
    code.refresh_from_db()
    assert code.consumed_at is not None
    # Welcome email sent
    assert any("Bienvenido" in m.subject or "Welcome" in m.subject for m in mail.outbox)


@pytest.mark.django_db
def test_verify_wrong_code_increments_attempts(api_client, user_with_code):
    user, code = user_with_code
    response = api_client.post(VERIFY_URL, {"email": user.email, "code": "000000"}, format="json")
    assert response.status_code == 400
    assert response.json()["code"] == ["invalid"]
    code.refresh_from_db()
    assert code.attempts == 1
    assert code.consumed_at is None


@pytest.mark.django_db
def test_verify_expired_code(api_client, user_with_code):
    user, code = user_with_code
    code.expires_at = timezone.now() - timedelta(seconds=1)
    code.save(update_fields=["expires_at"])
    response = api_client.post(VERIFY_URL, {"email": user.email, "code": code.code}, format="json")
    assert response.status_code == 400
    assert response.json()["code"] == ["expired"]
    user.refresh_from_db()
    assert user.is_email_verified is False


@pytest.mark.django_db
def test_verify_locks_after_max_attempts(api_client, user_with_code, settings):
    user, code = user_with_code
    settings.EMAIL_VERIFICATION_MAX_ATTEMPTS = 3
    for _ in range(3):
        api_client.post(VERIFY_URL, {"email": user.email, "code": "000000"}, format="json")
    code.refresh_from_db()
    assert code.consumed_at is not None  # forcibly consumed after lockout
    # Even the correct code now fails because the code was invalidated.
    response = api_client.post(VERIFY_URL, {"email": user.email, "code": code.code}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_verify_unknown_email_returns_400_without_leaking(api_client):
    response = api_client.post(
        VERIFY_URL, {"email": "ghost@layapa.test", "code": "123456"}, format="json"
    )
    assert response.status_code == 400
    # Same shape as a bad code on a real account.
    assert response.json() == {"code": ["invalid"]}


@pytest.mark.django_db
def test_resend_issues_new_code_for_unverified_user(api_client, user_with_code):
    user, old = user_with_code
    response = api_client.post(RESEND_URL, {"email": user.email}, format="json")
    assert response.status_code == 202
    old.refresh_from_db()
    assert old.consumed_at is not None  # invalidated by `issue`
    assert EmailVerificationCode.objects.filter(user=user, consumed_at__isnull=True).exists()


@pytest.mark.django_db
def test_resend_is_silent_for_already_verified_user(api_client, consumer_user):
    response = api_client.post(RESEND_URL, {"email": consumer_user.email}, format="json")
    assert response.status_code == 202
    assert not EmailVerificationCode.objects.filter(user=consumer_user).exists()
