"""URLs for /api/v1/consumer/*."""

from django.urls import path

from . import orders_views, views

app_name = "consumer"

urlpatterns = [
    path("bags", views.BagListView.as_view(), name="bag-list"),
    path("bags/<uuid:pk>", views.BagDetailView.as_view(), name="bag-detail"),
    path("bags/<uuid:pk>/reviews", views.BagReviewsView.as_view(), name="bag-reviews"),
    path(
        "business-locations/<int:pk>/favorite",
        views.FavoriteToggleView.as_view(),
        name="favorite-toggle",
    ),
    path("orders", orders_views.OrderListView.as_view(), name="order-list"),
    path("orders/<uuid:pk>", orders_views.OrderDetailView.as_view(), name="order-detail"),
    path(
        "orders/<uuid:pk>/cancel",
        orders_views.OrderCancelView.as_view(),
        name="order-cancel",
    ),
    path(
        "orders/<uuid:pk>/redeem-credit",
        orders_views.OrderRedeemCreditView.as_view(),
        name="order-redeem-credit",
    ),
    path(
        "bonus-credits",
        orders_views.BonusCreditListView.as_view(),
        name="bonus-credits",
    ),
]
