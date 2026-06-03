"""URLs for /api/v1/users/me."""

from django.urls import path

from .views import MeView

app_name = "users"

urlpatterns = [
    path("me", MeView.as_view(), name="me"),
]
