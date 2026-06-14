from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse

from apps.users.models import User


@pytest.mark.django_db
def test_sales_rep_can_create_draft_business_account(authed_sales_rep):
    response = authed_sales_rep.post(
        reverse("v1:ops:sales-business-account-create"),
        {
            "owner_email": "nuevo-negocio@layapa.test",
            "owner_phone": "0999999999",
            "business_name": "Panaderia Nueva",
            "business_type": "bakery",
            "tier": "formal",
            "description": "Negocio cargado por ventas",
            "location_name": "Sucursal Centro",
            "address": "Calle Larga 123",
            "lat": -2.9,
            "lng": -79.0,
        },
        format="json",
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["name"] == "Panaderia Nueva"
    owner = User.objects.get(email="nuevo-negocio@layapa.test")
    assert owner.role == User.Role.BUSINESS_OWNER
    assert owner.is_email_verified is True


@pytest.mark.django_db
def test_send_business_setup_link_uses_reset_token_email(authed_admin, pending_business):
    response = authed_admin.post(
        reverse("v1:ops:sales-business-account-send-setup-link", args=[pending_business.id]),
        {},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["sent"] is True
    assert len(mail.outbox) == 1
    assert "Configura tu contraseña" in mail.outbox[0].subject
