"""GET + PATCH /api/v1/users/me."""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.users.models import ConsumerProfile

URL = reverse("v1:users:me")


@pytest.mark.django_db
def test_me_get_requires_auth(api_client):
    response = api_client.get(URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_me_get_returns_consumer_with_profile(authed_client, consumer_user):
    response = authed_client.get(URL)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == consumer_user.email
    assert body["role"] == "consumer"
    assert body["consumer_profile"]["first_name"] == "Maya"
    assert "referral_code" in body["consumer_profile"]
    assert body["business_summary"] is None
    # Onboarding is incomplete: no dietary tags yet.
    assert body["onboarding_completed"] is False


@pytest.mark.django_db
def test_me_get_business_owner_has_no_consumer_profile(api_client, business_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(business_user).access_token}"
    )
    response = api_client.get(URL)
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "business_owner"
    assert body["consumer_profile"] is None
    assert body["business_summary"] is None
    assert body["onboarding_completed"] is False


@pytest.mark.django_db
def test_me_patch_updates_first_name_and_dietary(authed_client, dietary_tags, consumer_user):
    response = authed_client.patch(
        URL,
        {"first_name": "Mateo", "dietary_preferences": ["vegan", "gluten_free"]},
        format="json",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["consumer_profile"]["first_name"] == "Mateo"
    assert set(body["consumer_profile"]["dietary_preferences"]) == {"vegan", "gluten_free"}
    assert body["onboarding_completed"] is True


@pytest.mark.django_db
def test_me_patch_updates_language_on_user_model(authed_client, consumer_user):
    response = authed_client.patch(URL, {"language": "en"}, format="json")
    assert response.status_code == 200
    consumer_user.refresh_from_db()
    assert consumer_user.language == "en"


@pytest.mark.django_db
def test_me_patch_creates_consumer_profile_if_missing(api_client, dietary_tags):
    """A user created without a ConsumerProfile (edge case) gets one on first PATCH."""
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.users.factories import UserFactory

    user = UserFactory(email="solo@layapa.test", is_email_verified=True)
    ConsumerProfile.objects.filter(user=user).delete()  # force the edge case
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")

    response = api_client.patch(
        URL,
        {"first_name": "Solo", "dietary_preferences": ["vegan"]},
        format="json",
    )
    assert response.status_code == 200
    assert ConsumerProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_me_patch_rejects_invalid_location(authed_client):
    response = authed_client.patch(URL, {"default_location": "not-a-dict"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_me_patch_does_not_allow_changing_email_or_role(authed_client, consumer_user):
    response = authed_client.patch(
        URL,
        {"email": "hijack@layapa.test", "role": "admin"},
        format="json",
    )
    # Unknown fields are silently ignored by serializers.Serializer; assert side-effect.
    consumer_user.refresh_from_db()
    assert consumer_user.email == "consumer@layapa.test"
    assert consumer_user.role == "consumer"
    assert response.status_code == 200
