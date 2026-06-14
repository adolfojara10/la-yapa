from __future__ import annotations

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.businesses.factories import (
    BusinessFactory,
    BusinessLocationFactory,
    BusinessVerificationFactory,
)
from apps.businesses.models import BusinessStatus
from apps.users.factories import AdminUserFactory, UserFactory
from apps.users.models import User


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_user(db):
    return AdminUserFactory(email="admin@layapa.test", is_email_verified=True)


@pytest.fixture
def sales_rep_user(db):
    return UserFactory(role=User.Role.SALES_REP, email="rep@layapa.test", is_email_verified=True)


@pytest.fixture
def authed_admin(api_client, admin_user):
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(admin_user).access_token}"
    )
    return api_client


@pytest.fixture
def authed_sales_rep(api_client, sales_rep_user):
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(sales_rep_user).access_token}"
    )
    return api_client


@pytest.fixture
def pending_business(db):
    business = BusinessFactory(status=BusinessStatus.PENDING, name="Mercado Prueba")
    BusinessLocationFactory(business=business, name="Puesto Central")
    BusinessVerificationFactory(business=business)
    return business
