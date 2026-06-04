"""Shared fixtures for orders + payments tests."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.bags.factories import BagFactory
from apps.users.factories import ConsumerProfileFactory, UserFactory


@pytest.fixture
def consumer(db):
    user = UserFactory(email="shopper@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=user)
    return user


@pytest.fixture
def consumer_b(db):
    """Second consumer used for cross-user-access tests."""
    user = UserFactory(email="other@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=user)
    return user


@pytest.fixture
def fresh_bag(db):
    return BagFactory(
        original_price=Decimal("12.00"),
        sale_price=Decimal("4.50"),
        quantity_available=5,
        pickup_window_start=timezone.now() + timedelta(hours=4),
        pickup_window_end=timezone.now() + timedelta(hours=6),
    )


@pytest.fixture
def low_stock_bag(db):
    return BagFactory(
        original_price=Decimal("10.00"),
        sale_price=Decimal("3.00"),
        quantity_available=1,
        pickup_window_start=timezone.now() + timedelta(hours=4),
        pickup_window_end=timezone.now() + timedelta(hours=6),
    )
