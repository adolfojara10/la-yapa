"""Factories for suspended-meal donations."""

from __future__ import annotations

from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from apps.users.factories import UserFactory

from .models import DonationStatus, SuspendedMealDonation


class SuspendedMealDonationFactory(DjangoModelFactory):
    class Meta:
        model = SuspendedMealDonation

    donor = factory.SubFactory(UserFactory)
    amount = Decimal("4.50")
    bag = None  # general pool by default; tests override for bag-specific
    status = DonationStatus.ACTIVE
    is_anonymous = True
