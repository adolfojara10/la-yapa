"""Review factory."""

from __future__ import annotations

import factory
from factory.django import DjangoModelFactory

from apps.orders.factories import OrderFactory

from .models import Review


class ReviewFactory(DjangoModelFactory):
    class Meta:
        model = Review

    order = factory.SubFactory(OrderFactory)
    consumer = factory.LazyAttribute(lambda o: o.order.consumer)
    business_location = factory.LazyAttribute(lambda o: o.order.business_location)
    rating = 5
    comment = ""
    is_visible = True
