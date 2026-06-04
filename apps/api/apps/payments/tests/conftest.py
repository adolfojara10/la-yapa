"""Shared fixtures for payment tests."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.bags.factories import BagFactory
from apps.orders.services import create_order
from apps.users.factories import ConsumerProfileFactory, UserFactory


@pytest.fixture
def consumer(db):
    user = UserFactory(email="payer@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=user)
    return user


@pytest.fixture
def consumer_b(db):
    user = UserFactory(email="payer-b@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=user)
    return user


@pytest.fixture
def authed(consumer):
    client = APIClient()
    refresh = RefreshToken.for_user(consumer)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def pending_order(consumer):
    bag = BagFactory(
        original_price=Decimal("12.00"),
        sale_price=Decimal("4.50"),
        quantity_available=3,
        pickup_window_start=timezone.now() + timedelta(hours=4),
        pickup_window_end=timezone.now() + timedelta(hours=6),
    )
    return create_order(consumer=consumer, bag_id=bag.id, quantity=1)
