"""Role-based DRF permissions."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from apps.users.auth.permissions import (
    AdminOnly,
    AdminOrSalesRepOnly,
    BusinessOwnerOnly,
    ConsumerOnly,
    IsEmailVerified,
    SalesRepOnly,
)
from apps.users.factories import AdminUserFactory, BusinessOwnerFactory, UserFactory


def _request_for(user):
    req = Mock()
    req.user = user
    return req


@pytest.mark.django_db
def test_consumer_only_allows_consumers_rejects_others():
    consumer = UserFactory()
    biz = BusinessOwnerFactory()
    admin = AdminUserFactory()
    perm = ConsumerOnly()
    assert perm.has_permission(_request_for(consumer), None) is True
    assert perm.has_permission(_request_for(biz), None) is False
    assert perm.has_permission(_request_for(admin), None) is False


@pytest.mark.django_db
def test_business_owner_only():
    biz = BusinessOwnerFactory()
    consumer = UserFactory()
    perm = BusinessOwnerOnly()
    assert perm.has_permission(_request_for(biz), None) is True
    assert perm.has_permission(_request_for(consumer), None) is False


@pytest.mark.django_db
def test_admin_only():
    admin = AdminUserFactory()
    consumer = UserFactory()
    perm = AdminOnly()
    assert perm.has_permission(_request_for(admin), None) is True
    assert perm.has_permission(_request_for(consumer), None) is False


@pytest.mark.django_db
def test_sales_rep_only():
    from apps.users.models import User

    rep = UserFactory(role=User.Role.SALES_REP)
    consumer = UserFactory()
    perm = SalesRepOnly()
    assert perm.has_permission(_request_for(rep), None) is True
    assert perm.has_permission(_request_for(consumer), None) is False


@pytest.mark.django_db
def test_admin_or_sales_rep_only():
    from apps.users.models import User

    admin = AdminUserFactory()
    rep = UserFactory(role=User.Role.SALES_REP)
    consumer = UserFactory()
    perm = AdminOrSalesRepOnly()
    assert perm.has_permission(_request_for(admin), None) is True
    assert perm.has_permission(_request_for(rep), None) is True
    assert perm.has_permission(_request_for(consumer), None) is False


@pytest.mark.django_db
def test_email_verified_gate():
    verified = UserFactory(is_email_verified=True)
    unverified = UserFactory(is_email_verified=False)
    perm = IsEmailVerified()
    assert perm.has_permission(_request_for(verified), None) is True
    assert perm.has_permission(_request_for(unverified), None) is False


def test_unauthenticated_request_always_denied():
    anon = Mock()
    anon.is_authenticated = False
    req = Mock()
    req.user = anon
    for cls in (
        ConsumerOnly,
        BusinessOwnerOnly,
        AdminOnly,
        SalesRepOnly,
        AdminOrSalesRepOnly,
        IsEmailVerified,
    ):
        assert cls().has_permission(req, None) is False
