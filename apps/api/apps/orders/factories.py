"""Order factory."""

from __future__ import annotations

from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.bags.factories import BagFactory
from apps.users.factories import UserFactory

from .models import Order, OrderStatus, PaymentMethod


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    consumer = factory.SubFactory(UserFactory)
    bag = factory.SubFactory(BagFactory)
    business_location = factory.LazyAttribute(lambda o: o.bag.business_location)
    quantity = 1
    original_price_snapshot = factory.LazyAttribute(lambda o: o.bag.original_price)
    sale_price_snapshot = factory.LazyAttribute(lambda o: o.bag.sale_price)
    total_paid = factory.LazyAttribute(lambda o: o.sale_price_snapshot * o.quantity)
    platform_commission = factory.LazyAttribute(
        lambda o: (o.total_paid * Decimal("0.18")).quantize(Decimal("0.01"))
    )
    business_payout_amount = factory.LazyAttribute(
        lambda o: (o.total_paid - o.platform_commission).quantize(Decimal("0.01"))
    )
    status = OrderStatus.PAID
    payment_method = PaymentMethod.PAYPHONE
