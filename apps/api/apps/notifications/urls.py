"""URLs for /api/v1/notifications/*."""

from django.urls import path

from .views import RegisterPushTokenView

app_name = "notifications"

urlpatterns = [
    path("register-token", RegisterPushTokenView.as_view(), name="register-token"),
]
