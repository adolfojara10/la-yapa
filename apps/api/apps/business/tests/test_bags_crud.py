from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from apps.bags.factories import AllergenTagFactory, BagFactory
from apps.orders.models import OrderStatus
from apps.orders.services import create_order
from apps.users.factories import DietaryTagFactory


def _image() -> SimpleUploadedFile:
    return SimpleUploadedFile("bag.jpg", b"img", content_type="image/jpeg")


@pytest.mark.django_db
def test_bag_crud_duplicate_and_templates(authed, location):
    DietaryTagFactory(name="vegan")
    AllergenTagFactory(name="gluten")

    create_response = authed.post(
        reverse("v1:business:bags"),
        {
            "business_location_id": str(location.id),
            "type": "surprise",
            "title": "Pan del dia",
            "description": "Bolsa del horno",
            "original_price": "9.00",
            "sale_price": "3.00",
            "quantity_available": "4",
            "pickup_window_start": (timezone.now() + timedelta(hours=2)).isoformat(),
            "pickup_window_end": (timezone.now() + timedelta(hours=4)).isoformat(),
            "dietary_tags": '["vegan"]',
            "allergen_warnings": '["gluten"]',
            "is_suspended_meal_eligible": "true",
            "image": _image(),
        },
        format="multipart",
    )
    assert create_response.status_code == 201, create_response.content
    bag_id = create_response.json()["id"]

    detail_response = authed.patch(
        reverse("v1:business:bag-detail", args=[bag_id]),
        {"title": "Pan sorpresa del dia"},
        format="json",
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Pan sorpresa del dia"

    duplicate_response = authed.post(
        reverse("v1:business:bag-duplicate", args=[bag_id]),
        {},
        format="json",
    )
    assert duplicate_response.status_code == 201
    assert duplicate_response.json()["title"] == "Pan sorpresa del dia"

    template_create = authed.post(
        reverse("v1:business:bag-templates"),
        {
            "name": "Pan del dia",
            "type": "surprise",
            "title": "Pan sorpresa del dia",
            "description": "Plantilla reusable",
            "original_price": "9.00",
            "sale_price": "3.00",
            "dietary_tags": '["vegan"]',
            "allergen_warnings": '["gluten"]',
        },
        format="json",
    )
    assert template_create.status_code == 201, template_create.content

    templates_list = authed.get(reverse("v1:business:bag-templates"))
    assert templates_list.status_code == 200
    assert len(templates_list.json()) == 1


@pytest.mark.django_db
def test_bag_edit_blocked_after_sale(authed, location, consumer):
    bag = BagFactory(
        business_location=location,
        pickup_window_start=timezone.now() + timedelta(hours=2),
        pickup_window_end=timezone.now() + timedelta(hours=4),
    )
    order = create_order(consumer=consumer, bag_id=bag.id, quantity=1)
    order.status = OrderStatus.PAID
    order.save(update_fields=["status"])

    response = authed.patch(
        reverse("v1:business:bag-detail", args=[bag.id]),
        {"title": "Nuevo titulo"},
        format="json",
    )
    assert response.status_code == 409
    assert response.json()["code"] == "bag_edit_not_allowed"


@pytest.mark.django_db
def test_bag_create_rejects_past_pickup_window(authed, location):
    response = authed.post(
        reverse("v1:business:bags"),
        {
            "business_location_id": location.id,
            "type": "surprise",
            "title": "Bolsa vencida",
            "original_price": "9.00",
            "sale_price": "3.00",
            "quantity_available": 4,
            "pickup_window_start": (timezone.now() - timedelta(hours=1)).isoformat(),
            "pickup_window_end": (timezone.now() + timedelta(hours=1)).isoformat(),
        },
        format="json",
    )
    assert response.status_code == 400
    assert "pickup_window_start" in response.json()
