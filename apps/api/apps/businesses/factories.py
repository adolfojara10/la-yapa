"""Factories for businesses, locations, verifications, favorites."""

from __future__ import annotations

import factory
from factory.django import DjangoModelFactory
from faker import Faker

from apps.geo.utils import make_point
from apps.users.factories import BusinessOwnerFactory, UserFactory

from .models import (
    Business,
    BusinessLocation,
    BusinessStatus,
    BusinessTier,
    BusinessType,
    BusinessVerification,
    Favorite,
)

fake = Faker("es_ES")


class BusinessFactory(DjangoModelFactory):
    class Meta:
        model = Business

    owner = factory.SubFactory(BusinessOwnerFactory)
    name = factory.LazyFunction(lambda: fake.company())
    business_type = factory.Iterator([c.value for c in BusinessType if c != BusinessType.OTHER])
    tier = BusinessTier.FORMAL
    status = BusinessStatus.APPROVED
    description = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=2))
    phone = factory.LazyFunction(lambda: fake.phone_number()[:20])
    email = factory.LazyAttribute(lambda o: f"contacto@{o.name.split()[0].lower()}.test")


class BusinessLocationFactory(DjangoModelFactory):
    class Meta:
        model = BusinessLocation

    business = factory.SubFactory(BusinessFactory)
    name = factory.Iterator(["Sucursal Centro", "Sucursal Norte", "Sucursal Sur"])
    address = factory.LazyFunction(lambda: fake.street_address())
    # Cuenca-ish: -2.9001, -79.0059 ± jitter
    location = factory.LazyAttribute(
        lambda _: make_point(
            -2.9001 + (fake.random_number(digits=3) - 500) / 10_000,
            -79.0059 + (fake.random_number(digits=3) - 500) / 10_000,
        )
    )
    phone = factory.LazyFunction(lambda: fake.phone_number()[:20])
    is_active = True


class BusinessVerificationFactory(DjangoModelFactory):
    class Meta:
        model = BusinessVerification

    business = factory.SubFactory(BusinessFactory)
    ruc_number = factory.Sequence(lambda n: f"170000{n:04d}001")
    cedula_number = factory.Sequence(lambda n: f"010{n:07d}")


class FavoriteFactory(DjangoModelFactory):
    class Meta:
        model = Favorite

    user = factory.SubFactory(UserFactory)
    business_location = factory.SubFactory(BusinessLocationFactory)
