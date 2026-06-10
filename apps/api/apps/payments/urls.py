"""URLs for /api/v1/payments/*."""

from django.urls import path

from .views import ChargeView, DeUnaWebhookView, FakeCheckoutView, PayPhoneWebhookView

app_name = "payments"

urlpatterns = [
    path("charge", ChargeView.as_view(), name="charge"),
    path("payphone/webhook", PayPhoneWebhookView.as_view(), name="payphone-webhook"),
    path("de-una/webhook", DeUnaWebhookView.as_view(), name="de-una-webhook"),
    path("fake/checkout/<str:tx_id>", FakeCheckoutView.as_view(), name="fake-checkout"),
]
