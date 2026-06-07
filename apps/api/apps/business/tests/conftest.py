"""Shared fixtures for /api/v1/business/ tests."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.bags.factories import BagFactory
from apps.businesses.factories import BusinessFactory, BusinessLocationFactory
from apps.orders.models import OrderStatus
from apps.orders.services import create_order
from apps.users.factories import (
    BusinessOwnerFactory,
    ConsumerProfileFactory,
    UserFactory,
)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def business_owner(db):
    user = BusinessOwnerFactory(email="owner@layapa.test", is_email_verified=True)
    return user


@pytest.fixture
def other_owner(db):
    """A second owner used for cross-business isolation tests."""
    return BusinessOwnerFactory(email="other-owner@layapa.test", is_email_verified=True)


@pytest.fixture
def business(business_owner):
    biz = BusinessFactory(owner=business_owner, name="Panadería de Pruebas")
    return biz


@pytest.fixture
def location(business):
    return BusinessLocationFactory(business=business, name="Sucursal Centro")


@pytest.fixture
def authed(api_client, business_owner):
    refresh = RefreshToken.for_user(business_owner)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def consumer(db):
    user = UserFactory(email="buyer@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=user, first_name="Mateo")
    return user


@pytest.fixture
def paid_order(consumer, location):
    """A PAID order at `location` whose pickup window is open NOW.

    Bypasses the payment webhook for test convenience — we directly set
    status to PAID after create_order returns.
    """
    bag = BagFactory(
        business_location=location,
        original_price=Decimal("12.00"),
        sale_price=Decimal("4.50"),
        quantity_available=5,
        pickup_window_start=timezone.now() - timedelta(minutes=10),
        pickup_window_end=timezone.now() + timedelta(minutes=50),
    )
    order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])
    return order
