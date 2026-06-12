from __future__ import annotations

import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.businesses.models import BusinessStatus, BusinessVerification
from apps.users.factories import UserFactory
from apps.users.models import User


def _upload(name: str, content_type: str = "application/pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, b"file-bytes", content_type=content_type)


@pytest.mark.django_db
def test_business_onboarding_formal_creates_pending_business_and_notifies_sales(
    authed, business_owner
):
    sent = []

    def fake_send_mail(*args, **kwargs):
        sent.append({"args": args, "kwargs": kwargs})
        return 1

    UserFactory(role=User.Role.SALES_REP, email="sales@layapa.test", is_active=True)

    import apps.business.services as services

    services.send_mail = fake_send_mail

    response = authed.post(
        reverse("v1:business:onboarding"),
        {
            "name": "Panaderia Sol",
            "business_type": "bakery",
            "tier": "formal",
            "description": "Pan del dia",
            "phone": "0999999999",
            "email": "panaderia@layapa.test",
            "location_name": "Sucursal Centro",
            "address": "Calle Larga 123",
            "lat": "-2.90",
            "lng": "-79.00",
            "hours_of_operation": json.dumps({"mon": "08:00-17:00"}),
            "payout_method": "bank_transfer",
            "payout_frequency": "weekly",
            "account_holder": "Maria Perez",
            "bank_name": "Pichincha",
            "account_number": "1234567890",
            "account_type": "checking",
            "cedula_number": "0102030405",
            "ruc_number": "0102030405001",
            "has_food_handling": "true",
            "food_safety_terms_accepted": "true",
            "ruc_document": _upload("ruc.pdf"),
            "cedula_document": _upload("cedula.pdf"),
            "permiso_funcionamiento": _upload("permiso.pdf"),
            "arcsa_document": _upload("arcsa.pdf"),
            "bank_proof": _upload("bank.pdf"),
        },
        format="multipart",
    )

    assert response.status_code == 201, response.content
    business_owner.refresh_from_db()
    business = business_owner.businesses.get()
    assert business.status == BusinessStatus.PENDING
    assert business.locations.count() == 1
    verification = BusinessVerification.objects.get(business=business)
    assert verification.ruc_document_url
    assert verification.arcsa_url
    assert verification.food_safety_terms_accepted_at is not None
    assert response.json()["status"] == "pending"
    assert len(sent) == 1


@pytest.mark.django_db
def test_business_onboarding_informal_requires_selfie_and_business_photo(authed):
    response = authed.post(
        reverse("v1:business:onboarding"),
        {
            "name": "Mercado Verde",
            "business_type": "mercado",
            "tier": "informal",
            "location_name": "Puesto 12",
            "address": "Mercado 10 de Agosto",
            "lat": "-2.91",
            "lng": "-79.01",
            "payout_method": "de_una",
            "account_holder": "Juan Perez",
            "deuna_phone": "0991112233",
            "cedula_number": "0102030405",
            "food_safety_terms_accepted": "true",
            "cedula_document": _upload("cedula.pdf"),
        },
        format="multipart",
    )

    assert response.status_code == 400
    body = response.json()
    assert "selfie_with_cedula" in body or "business_photo" in body


@pytest.mark.django_db
def test_me_includes_business_summary_after_onboarding(authed, business_owner):
    authed.post(
        reverse("v1:business:onboarding"),
        {
            "name": "Mercado Verde",
            "business_type": "mercado",
            "tier": "informal",
            "location_name": "Puesto 12",
            "address": "Mercado 10 de Agosto",
            "lat": "-2.91",
            "lng": "-79.01",
            "payout_method": "de_una",
            "account_holder": "Juan Perez",
            "deuna_phone": "0991112233",
            "cedula_number": "0102030405",
            "food_safety_terms_accepted": "true",
            "cedula_document": _upload("cedula.pdf"),
            "selfie_with_cedula": _upload("selfie.jpg", "image/jpeg"),
            "business_photo": _upload("puesto.jpg", "image/jpeg"),
        },
        format="multipart",
    )

    response = authed.get(reverse("v1:users:me"))
    assert response.status_code == 200
    body = response.json()
    assert body["onboarding_completed"] is True
    assert body["business_summary"]["name"] == "Mercado Verde"
    assert body["business_summary"]["status"] == "pending"
