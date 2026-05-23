"""Bag + allergen factories."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.businesses.factories import BusinessLocationFactory

from .models import AllergenTag, Bag, BagType


class AllergenTagFactory(DjangoModelFactory):
    class Meta:
        model = AllergenTag
        django_get_or_create = ("name",)

    name = factory.Iterator(["mani", "gluten", "lacteos", "frutos_secos", "mariscos"])
    label_es = factory.LazyAttribute(lambda o: o.name.replace("_", " ").title())


class BagFactory(DjangoModelFactory):
    class Meta:
        model = Bag

    business_location = factory.SubFactory(BusinessLocationFactory)
    type = BagType.SURPRISE
    title = factory.Sequence(lambda n: f"Bolsa Sorpresa #{n}")
    description = "Una selección de productos del día."
    original_price = Decimal("12.00")
    sale_price = Decimal("4.50")
    quantity_available = 5
    pickup_window_start = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=2))
    pickup_window_end = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=4))
    is_active = True
