"""Shared fixtures for users/auth tests."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.users.factories import (
    BusinessOwnerFactory,
    ConsumerProfileFactory,
    DietaryTagFactory,
    UserFactory,
)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def consumer_user(db):
    user = UserFactory(email="consumer@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=user, first_name="Maya")
    return user


@pytest.fixture
def business_user(db):
    return BusinessOwnerFactory(email="biz@layapa.test", is_email_verified=True)


@pytest.fixture
def dietary_tags(db):
    return [DietaryTagFactory(name=n) for n in ("vegan", "gluten_free", "vegetarian")]


@pytest.fixture
def authed_client(api_client, consumer_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(consumer_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client
