"""URLs for /api/v1/geo/*."""

from django.urls import path

from .views import GeoReverseView, GeoSearchView

app_name = "geo"

urlpatterns = [
    path("search", GeoSearchView.as_view(), name="search"),
    path("reverse", GeoReverseView.as_view(), name="reverse"),
]
