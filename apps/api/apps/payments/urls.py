"""URLs for /api/v1/payments/*."""

from django.urls import path

from .views import ChargeView, DeUnaWebhookView, PayPhoneWebhookView

app_name = "payments"

urlpatterns = [
    path("charge", ChargeView.as_view(), name="charge"),
    path("payphone/webhook", PayPhoneWebhookView.as_view(), name="payphone-webhook"),
    path("de-una/webhook", DeUnaWebhookView.as_view(), name="de-una-webhook"),
]
