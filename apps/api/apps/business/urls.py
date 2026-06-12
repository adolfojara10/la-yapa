"""URLs for /api/v1/business/*."""

from django.urls import path

from . import views

app_name = "business"

urlpatterns = [
    path("onboarding", views.OnboardingView.as_view(), name="onboarding"),
    path("locations", views.LocationsView.as_view(), name="locations"),
    path("locations/<int:pk>", views.LocationDetailView.as_view(), name="location-detail"),
    path("bags", views.BagsView.as_view(), name="bags"),
    path("bags/<uuid:pk>", views.BagDetailView.as_view(), name="bag-detail"),
    path("bags/<uuid:pk>/duplicate", views.BagDuplicateView.as_view(), name="bag-duplicate"),
    path("bag-templates", views.BagTemplatesView.as_view(), name="bag-templates"),
    path(
        "bag-templates/<uuid:pk>",
        views.BagTemplateDetailView.as_view(),
        name="bag-template-detail",
    ),
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
