from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse

from apps.businesses.models import BusinessStatus


@pytest.mark.django_db
def test_admin_session_requires_ops_role(api_client):
    api_client.credentials = None
    response = api_client.get(reverse("v1:ops:session"))
    assert response.status_code == 401


@pytest.mark.django_db
def test_business_list_filters_pending(authed_admin, pending_business):
    response = authed_admin.get(reverse("v1:ops:business-list"), {"status": "pending"})
    assert response.status_code == 200
    assert response.json()[0]["id"] == pending_business.id


@pytest.mark.django_db
def test_business_detail_includes_locations_and_verification(authed_admin, pending_business):
    response = authed_admin.get(reverse("v1:ops:business-detail", args=[pending_business.id]))
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == pending_business.name
    assert len(body["locations"]) == 1
    assert body["verification"]["cedula_number"]


@pytest.mark.django_db
def test_approve_business_updates_status_and_sends_email(
    authed_admin, pending_business, admin_user
):
    response = authed_admin.post(reverse("v1:ops:business-approve", args=[pending_business.id]), {})
    assert response.status_code == 200
    pending_business.refresh_from_db()
    assert pending_business.status == BusinessStatus.APPROVED
    assert pending_business.approved_by_id == admin_user.id
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_reject_business_requires_reason_and_notifies(authed_admin, pending_business):
    url = reverse("v1:ops:business-reject", args=[pending_business.id])
    missing_reason = authed_admin.post(url, {}, format="json")
    assert missing_reason.status_code == 400

    response = authed_admin.post(url, {"reason": "Documento ilegible"}, format="json")
    assert response.status_code == 200
    pending_business.refresh_from_db()
    assert pending_business.status == BusinessStatus.REJECTED
    assert pending_business.rejection_reason == "Documento ilegible"
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_request_more_info_keeps_pending_and_stores_notes(authed_sales_rep, pending_business):
    url = reverse("v1:ops:business-request-more-info", args=[pending_business.id])
    response = authed_sales_rep.post(
        url,
        {"reason": "Sube una foto mas clara del permiso."},
        format="json",
    )
    assert response.status_code == 200
    pending_business.refresh_from_db()
    assert pending_business.status == BusinessStatus.PENDING
    assert pending_business.review_notes == "Sube una foto mas clara del permiso."
    assert len(mail.outbox) == 1
