"""URLs for /api/v1/business/*."""

from django.urls import path

from . import views

app_name = "business"

urlpatterns = [
    path("dashboard", views.DashboardView.as_view(), name="dashboard"),
    path("orders/active", views.ActiveOrdersView.as_view(), name="orders-active"),
    path("orders/today", views.TodayOrdersView.as_view(), name="orders-today"),
    path(
        "orders/confirm-pickup-by-scan",
        views.ConfirmPickupByScanView.as_view(),
        name="confirm-pickup-by-scan",
    ),
    path(
        "orders/confirm-pickup-by-pin",
        views.ConfirmPickupByPinView.as_view(),
        name="confirm-pickup-by-pin",
    ),
    path("orders/<uuid:pk>", views.OrderDetailView.as_view(), name="order-detail"),
    path(
        "orders/<uuid:pk>/confirm-pickup",
        views.ConfirmPickupByIdView.as_view(),
        name="confirm-pickup-by-id",
    ),
    path(
        "suspended-meals/active",
        views.ActiveSuspendedView.as_view(),
        name="suspended-active",
    ),
    path(
        "suspended-meals/dispatch",
        views.DispatchSuspendedView.as_view(),
        name="suspended-dispatch",
    ),
]
