"""Shared fixtures for /api/v1/consumer/ tests."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.bags.factories import AllergenTagFactory, BagFactory
from apps.businesses.factories import BusinessFactory, BusinessLocationFactory
from apps.users.factories import ConsumerProfileFactory, UserFactory
from apps.users.models import DietaryTag


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def consumer(db):
    user = UserFactory(email="browser@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=user, first_name="Maya")
    return user


@pytest.fixture
def authed(api_client, consumer):
    refresh = RefreshToken.for_user(consumer)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def vegan_tag(db):
    return DietaryTag.objects.create(name="vegan", label_es="Vegano")


@pytest.fixture
def gluten_free_tag(db):
    return DietaryTag.objects.create(name="gluten_free", label_es="Sin gluten")


@pytest.fixture
def gluten_allergen(db):
    return AllergenTagFactory(name="gluten", label_es="Gluten")


@pytest.fixture
def mani_allergen(db):
    return AllergenTagFactory(name="mani", label_es="Maní")


@pytest.fixture
def panaderia(db):
    """A second business so the seed `q` text-search test has something to find."""
    return BusinessFactory(name="Panadería La Esperanza")


@pytest.fixture
def panaderia_location(db, panaderia):
    return BusinessLocationFactory(business=panaderia)


def _bag(
    *,
    location=None,
    sale_price="4.50",
    original_price="12.00",
    hours_ahead: int = 2,
    duration_hours: int = 2,
    is_active: bool = True,
    quantity_available: int = 5,
    title: str | None = None,
    dietary: list | None = None,
    allergens: list | None = None,
):
    """Factory shortcut that lets tests focus on the param under test."""
    now = timezone.now()
    kwargs = {
        "sale_price": Decimal(sale_price),
        "original_price": Decimal(original_price),
        "pickup_window_start": now + timedelta(hours=hours_ahead),
        "pickup_window_end": now + timedelta(hours=hours_ahead + duration_hours),
        "is_active": is_active,
        "quantity_available": quantity_available,
    }
    if location is not None:
        kwargs["business_location"] = location
    if title is not None:
        kwargs["title"] = title
    bag = BagFactory(**kwargs)
    if dietary:
        bag.dietary_tags.set(dietary)
    if allergens:
        bag.allergen_warnings.set(allergens)
    return bag


@pytest.fixture
def make_bag():
    return _bag
