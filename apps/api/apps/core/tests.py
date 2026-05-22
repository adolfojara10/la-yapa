"""Smoke tests for the core app."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_returns_ok() -> None:
    client = APIClient()
    response = client.get(reverse("v1:health-check"))
    assert response.status_code == 200
    assert response.json()["service"] == "layapa-api"
