"""Business model tests."""

import pytest

from .factories import BusinessFactory, BusinessLocationFactory
from .models import BusinessStatus


@pytest.mark.django_db
def test_business_factory_defaults_to_approved():
    biz = BusinessFactory()
    assert biz.status == BusinessStatus.APPROVED


@pytest.mark.django_db
def test_business_location_inherits_business():
    loc = BusinessLocationFactory()
    assert loc.business.pk is not None
    assert loc.is_active is True


@pytest.mark.django_db
def test_approved_manager_filters_correctly():
    BusinessFactory(status=BusinessStatus.APPROVED)
    BusinessFactory(status=BusinessStatus.PENDING)
    from .models import Business

    assert Business.objects.approved().count() == 1


@pytest.mark.django_db
def test_bank_account_field_round_trips_encrypted():
    biz = BusinessFactory(bank_account='{"bank":"Pichincha","acct":"1234567890"}')
    biz.refresh_from_db()
    assert "Pichincha" in biz.bank_account
