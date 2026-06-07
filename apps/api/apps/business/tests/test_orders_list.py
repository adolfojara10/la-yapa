"""GET /api/v1/business/orders/active + /today + /{id} + /dashboard."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.bags.factories import BagFactory
from apps.businesses.factories import BusinessFactory, BusinessLocationFactory
from apps.orders.models import OrderStatus
from apps.orders.services import create_order
from apps.users.factories import (
    BusinessOwnerFactory,
)


def _bag_now(location):
    return BagFactory(
        business_location=location,
        original_price=Decimal("12.00"),
        sale_price=Decimal("4.50"),
        quantity_available=3,
        pickup_window_start=timezone.now() - timedelta(minutes=5),
        pickup_window_end=timezone.now() + timedelta(minutes=30),
    )


@pytest.mark.django_db
def test_active_orders_requires_business_owner_role(api_client, consumer):
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(consumer).access_token}"
    )
    response = api_client.get(reverse("v1:business:orders-active"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_active_orders_empty_when_no_business(api_client):
    """A business_owner with no Business rows sees an empty list, not 500."""
    user = BusinessOwnerFactory(is_email_verified=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    response = api_client.get(reverse("v1:business:orders-active"))
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_active_orders_lists_paid_orders_at_owned_location(
    authed, business_owner, location, consumer
):
    bag = _bag_now(location)
    order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])

    response = authed.get(reverse("v1:business:orders-active"))
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(order.id)
    assert body[0]["status"] == "paid"
    assert body[0]["consumer_first_name"] == "Mateo"
    assert body[0]["pickup_code"] == order.pickup_code


@pytest.mark.django_db
def test_active_orders_excludes_pending_payment(authed, location, consumer):
    """PENDING_PAYMENT orders haven't paid yet — vendors shouldn't see them."""
    bag = _bag_now(location)
    create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    response = authed.get(reverse("v1:business:orders-active"))
    assert response.json() == []


@pytest.mark.django_db
def test_active_orders_excludes_other_owners_orders(authed, consumer, other_owner):
    other_biz = BusinessFactory(owner=other_owner)
    other_loc = BusinessLocationFactory(business=other_biz)
    bag = _bag_now(other_loc)
    order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])

    response = authed.get(reverse("v1:business:orders-active"))
    assert response.json() == []


@pytest.mark.django_db
def test_today_orders_returns_terminal_today(authed, location, consumer):
    bag = _bag_now(location)
    order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    order.status = OrderStatus.COMPLETED
    order.picked_up_at = timezone.now()
    order.save(update_fields=["status", "picked_up_at"])

    response = authed.get(reverse("v1:business:orders-today"))
    assert response.status_code == 200
    ids = [o["id"] for o in response.json()]
    assert str(order.id) in ids


@pytest.mark.django_db
def test_order_detail_returns_own_order(authed, paid_order):
    url = reverse("v1:business:order-detail", args=[paid_order.id])
    response = authed.get(url)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(paid_order.id)
    assert body["bag"]["title"] == paid_order.bag.title


@pytest.mark.django_db
def test_order_detail_404_for_other_owner(api_client, paid_order):
    other = BusinessOwnerFactory(is_email_verified=True)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other).access_token}")
    response = api_client.get(reverse("v1:business:order-detail", args=[paid_order.id]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_consumer_payload_omits_email_and_last_name(authed, paid_order):
    response = authed.get(reverse("v1:business:order-detail", args=[paid_order.id]))
    body = response.json()
    payload_text = str(body)
    # Privacy: vendor sees first name only.
    assert "buyer@layapa.test" not in payload_text
    # last_name field should not appear (consumer hasn't set one anyway)
    assert "last_name" not in body
    assert body["consumer_first_name"] == "Mateo"


@pytest.mark.django_db
def test_dashboard_summary(authed, business_owner, location, consumer):
    # 1 active order
    bag1 = _bag_now(location)
    order1 = create_order(consumer=consumer, bag_id=bag1.id, quantity=1)
    order1.status = OrderStatus.PAID
    order1.save(update_fields=["status"])

    # 1 completed today
    bag2 = _bag_now(location)
    order2 = create_order(consumer=consumer, bag_id=bag2.id, quantity=1)
    order2.status = OrderStatus.COMPLETED
    order2.picked_up_at = timezone.now()
    order2.save(update_fields=["status", "picked_up_at"])

    response = authed.get(reverse("v1:business:dashboard"))
    body = response.json()
    assert body["active_orders_count"] == 1
    assert body["today_completed_count"] == 1
    assert body["suspended_meals_available"] == 0
