"""Order HTTP endpoints under /api/v1/consumer/orders."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.bags.factories import BagFactory
from apps.orders.models import OrderStatus
from apps.orders.services import create_order
from apps.payments.models import (
    BonusCredit,
    BonusCreditSource,
)


@pytest.fixture
def buyable_bag(db):
    return BagFactory(
        original_price=Decimal("12.00"),
        sale_price=Decimal("4.50"),
        quantity_available=3,
        pickup_window_start=timezone.now() + timedelta(hours=4),
        pickup_window_end=timezone.now() + timedelta(hours=6),
    )


@pytest.fixture
def soon_pickup_bag(db):
    """Pickup starts in 30 minutes — outside the 1h cancel window."""
    return BagFactory(
        original_price=Decimal("12.00"),
        sale_price=Decimal("4.50"),
        quantity_available=3,
        pickup_window_start=timezone.now() + timedelta(minutes=30),
        pickup_window_end=timezone.now() + timedelta(hours=2),
    )


@pytest.mark.django_db
def test_create_order_endpoint_happy_path(authed, buyable_bag):
    url = reverse("v1:consumer:order-list")
    response = authed.post(
        url,
        {"bag_id": str(buyable_bag.id), "quantity": 2},
        format="json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["status"] == "pending_payment"
    assert body["quantity"] == 2
    assert body["pickup_code"]


@pytest.mark.django_db
def test_create_order_endpoint_returns_409_when_oversold(authed, buyable_bag):
    """Quantity within the serializer's accepted range but exceeds bag stock."""
    buyable_bag.quantity_available = 1
    buyable_bag.save(update_fields=["quantity_available"])
    url = reverse("v1:consumer:order-list")
    response = authed.post(
        url,
        {"bag_id": str(buyable_bag.id), "quantity": 3},
        format="json",
    )
    assert response.status_code == 409
    assert response.json()["code"] == "insufficient_stock"


@pytest.mark.django_db
def test_create_order_persists_suspended_meal_flag(authed, buyable_bag):
    url = reverse("v1:consumer:order-list")
    response = authed.post(
        url,
        {
            "bag_id": str(buyable_bag.id),
            "quantity": 1,
            "donate_as_suspended_meal": True,
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["donate_as_suspended_meal"] is True


@pytest.mark.django_db
def test_list_orders_returns_only_own(authed, consumer, buyable_bag):
    create_order(consumer=consumer, bag_id=buyable_bag.id, quantity=1)
    # Other user's order should NOT appear.
    from apps.users.factories import ConsumerProfileFactory, UserFactory

    other = UserFactory(email="other@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=other)
    create_order(consumer=other, bag_id=buyable_bag.id, quantity=1)

    response = authed.get(reverse("v1:consumer:order-list"))
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 1
    assert body["results"][0]["bag"]["id"] == str(buyable_bag.id)


@pytest.mark.django_db
def test_order_detail_endpoint(authed, consumer, buyable_bag):
    order = create_order(consumer=consumer, bag_id=buyable_bag.id, quantity=1)
    url = reverse("v1:consumer:order-detail", args=[order.id])
    response = authed.get(url)
    assert response.status_code == 200
    assert response.json()["id"] == str(order.id)


@pytest.mark.django_db
def test_order_detail_404_for_other_consumer(api_client, buyable_bag):
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.users.factories import ConsumerProfileFactory, UserFactory

    owner = UserFactory(email="owner@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=owner)
    order = create_order(consumer=owner, bag_id=buyable_bag.id, quantity=1)

    snooper = UserFactory(email="snooper@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=snooper)
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(snooper).access_token}"
    )
    response = api_client.get(reverse("v1:consumer:order-detail", args=[order.id]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_cancel_endpoint_within_window(authed, consumer, buyable_bag):
    order = create_order(consumer=consumer, bag_id=buyable_bag.id, quantity=1)
    url = reverse("v1:consumer:order-cancel", args=[order.id])
    response = authed.post(url, {"reason": "changed mind"}, format="json")
    assert response.status_code == 200
    assert response.json()["order"]["status"] == "cancelled"


@pytest.mark.django_db
def test_cancel_endpoint_outside_window_returns_409(authed, consumer, soon_pickup_bag):
    order = create_order(consumer=consumer, bag_id=soon_pickup_bag.id, quantity=1)
    url = reverse("v1:consumer:order-cancel", args=[order.id])
    response = authed.post(url, {}, format="json")
    assert response.status_code == 409
    assert response.json()["code"] == "cancellation_outside_window"


@pytest.mark.django_db
def test_redeem_credit_endpoint(authed, consumer, buyable_bag):
    order = create_order(consumer=consumer, bag_id=buyable_bag.id, quantity=1)
    credit = BonusCredit.objects.create(
        user=consumer,
        amount=Decimal("2.00"),
        source=BonusCreditSource.PROMO,
    )
    url = reverse("v1:consumer:order-redeem-credit", args=[order.id])
    response = authed.post(url, {"credit_id": credit.id}, format="json")
    assert response.status_code == 200
    body = response.json()
    assert body["applied_credit_amount"] == "2.00"
    assert body["order"]["total_paid"] == "2.50"


@pytest.mark.django_db
def test_bonus_credits_list_endpoint(authed, consumer):
    BonusCredit.objects.create(
        user=consumer,
        amount=Decimal("1.00"),
        source=BonusCreditSource.BUSINESS_CANCELLATION,
    )
    response = authed.get(reverse("v1:consumer:bonus-credits"))
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["amount"] == "1.00"


@pytest.mark.django_db
def test_charge_endpoint_returns_webview_url(authed, consumer, buyable_bag):
    order = create_order(consumer=consumer, bag_id=buyable_bag.id, quantity=1)
    url = reverse("v1:payments:charge")
    response = authed.post(
        url,
        {
            "order_id": str(order.id),
            "provider": "payphone",
            "return_url": "layapa://payment-result",
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["webview_url"].startswith("https://fake.layapa.test/")
    assert body["provider"] == "payphone"


@pytest.mark.django_db
def test_charge_endpoint_rejects_paid_order(authed, consumer, buyable_bag):
    order = create_order(consumer=consumer, bag_id=buyable_bag.id, quantity=1)
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])
    url = reverse("v1:payments:charge")
    response = authed.post(
        url,
        {
            "order_id": str(order.id),
            "provider": "payphone",
            "return_url": "layapa://payment-result",
        },
        format="json",
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_status"


@pytest.mark.django_db
def test_charge_endpoint_404_for_others_order(api_client, buyable_bag):
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.users.factories import ConsumerProfileFactory, UserFactory

    owner = UserFactory(email="o@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=owner)
    order = create_order(consumer=owner, bag_id=buyable_bag.id, quantity=1)

    other = UserFactory(email="x@layapa.test", is_email_verified=True)
    ConsumerProfileFactory(user=other)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other).access_token}")
    url = reverse("v1:payments:charge")
    response = api_client.post(
        url,
        {
            "order_id": str(order.id),
            "provider": "payphone",
            "return_url": "layapa://payment-result",
        },
        format="json",
    )
    assert response.status_code == 404
