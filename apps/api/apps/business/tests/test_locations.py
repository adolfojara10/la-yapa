from __future__ import annotations

import json

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_locations_list_and_create(authed, location):
    list_response = authed.get(reverse("v1:business:locations"))
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    create_response = authed.post(
        reverse("v1:business:locations"),
        {
            "name": "Sucursal Norte",
            "address": "Av. Ordonez Lasso",
            "lat": -2.89,
            "lng": -79.02,
            "phone": "0990000000",
            "hours_of_operation": json.dumps({"sat": "08:00-14:00"}),
        },
        format="json",
    )
    assert create_response.status_code == 201, create_response.content
    assert create_response.json()["name"] == "Sucursal Norte"


@pytest.mark.django_db
def test_location_patch_can_disable(authed, location):
    response = authed.patch(
        reverse("v1:business:location-detail", args=[location.id]),
        {"is_active": False},
        format="json",
    )
    assert response.status_code == 200
    location.refresh_from_db()
    assert location.is_active is False
