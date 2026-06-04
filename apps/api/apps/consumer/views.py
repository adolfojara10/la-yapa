"""Consumer-facing read views (+ favorite toggle)."""

from __future__ import annotations

from django.db.models import Exists, OuterRef, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bags.models import Bag
from apps.businesses.models import BusinessLocation, Favorite
from apps.users.auth.permissions import ConsumerOnly, IsEmailVerified

from .filters import apply_filters, apply_sort
from .geo import annotate_distance, filter_within_radius, resolve_caller_location
from .pagination import BagCursorPagination
from .serializers import BagDetailSerializer, BagListSerializer, BagReviewSerializer

CONSUMER_PERMISSIONS = [IsAuthenticated, ConsumerOnly, IsEmailVerified]


class BagListView(GenericAPIView):
    """GET /api/v1/consumer/bags

    Returns a cursor-paginated list of active bags, filtered and sorted by
    the standard set of query params. See `filters.py` for the param table.
    """

    permission_classes = CONSUMER_PERMISSIONS
    serializer_class = BagListSerializer
    pagination_class = BagCursorPagination

    def get_queryset(self) -> QuerySet[Bag]:
        request = self.request
        params = request.query_params

        # Active bags only.
        qs = (
            Bag.objects.active()
            .select_related(
                "business_location__business",
            )
            .prefetch_related("dietary_tags", "allergen_warnings")
        )

        # Resolve location for distance annotations + radius filter.
        location = resolve_caller_location(params.get("lat"), params.get("lng"), request.user)
        if location is not None:
            lat, lng = location
            qs = annotate_distance(qs, lat, lng)
            radius_km = _parse_radius_km(params.get("radius_km"))
            qs = filter_within_radius(qs, lat, lng, radius_km=radius_km)

        # `is_favorited` annotation per request user — single subquery.
        qs = qs.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user=request.user,
                    business_location_id=OuterRef("business_location_id"),
                )
            )
        )

        qs = apply_filters(qs, params)
        qs = apply_sort(qs, params.get("sort"), has_location=location is not None)
        return qs

    def get(self, request, *args, **kwargs):
        qs = self.get_queryset()
        paginator = self.pagination_class()
        # Tell the paginator about the effective ordering so cursor encoding
        # matches the queryset.
        if qs.query.order_by:
            paginator.ordering = tuple(qs.query.order_by)
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = self.get_serializer(page or qs, many=True)
        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        return Response(serializer.data)


class BagDetailView(GenericAPIView):
    """GET /api/v1/consumer/bags/{id}"""

    permission_classes = CONSUMER_PERMISSIONS
    serializer_class = BagDetailSerializer

    def get(self, request, pk: str, *args, **kwargs):
        # Detail allows fetching expired/inactive bags so deep-links keep
        # working from notifications and emails; the `is_active` flag in
        # the response lets the client render a "no longer available" state.
        base_qs = Bag.objects.select_related(
            "business_location__business",
        ).prefetch_related("dietary_tags", "allergen_warnings")

        # Same annotation strategy as the list view: a single QuerySet that
        # carries distance_m + is_favorited so the serializer sees one
        # consistent shape.
        location = resolve_caller_location(
            request.query_params.get("lat"),
            request.query_params.get("lng"),
            request.user,
        )
        if location is not None:
            lat, lng = location
            base_qs = annotate_distance(base_qs, lat, lng)

        base_qs = base_qs.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    user=request.user,
                    business_location_id=OuterRef("business_location_id"),
                )
            )
        )

        bag = get_object_or_404(base_qs, pk=pk)

        # Attach rating aggregates so the embedded business payload stays
        # consistent with the list endpoint.
        from django.db.models import Avg as _Avg
        from django.db.models import Count as _Count

        loc = bag.business_location
        agg = loc.reviews.filter(is_visible=True).aggregate(avg=_Avg("rating"), cnt=_Count("id"))
        loc.rating_avg = agg["avg"]
        loc.rating_count = agg["cnt"]

        return Response(self.get_serializer(bag).data)


class BagReviewsView(GenericAPIView):
    """GET /api/v1/consumer/bags/{id}/reviews"""

    permission_classes = CONSUMER_PERMISSIONS
    serializer_class = BagReviewSerializer
    pagination_class = BagCursorPagination

    def get(self, request, pk: str, *args, **kwargs):
        bag = get_object_or_404(Bag.objects.only("id", "business_location_id"), pk=pk)
        qs = (
            bag.business_location.reviews.filter(is_visible=True)
            .select_related("consumer__consumer_profile")
            .order_by("-created_at", "id")
        )
        paginator = self.pagination_class()
        paginator.ordering = ("-created_at", "id")
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = self.get_serializer(page or qs, many=True)
        if page is not None:
            return paginator.get_paginated_response(serializer.data)
        return Response(serializer.data)


class FavoriteToggleView(APIView):
    """POST /api/v1/consumer/business-locations/{id}/favorite

    Toggles the favorite. Idempotent in spirit: returns the new state,
    not whether anything actually changed. Race-safe because we use
    delete-on-existing / create-on-missing inside a single request.
    """

    permission_classes = CONSUMER_PERMISSIONS

    def post(self, request, pk: int, *args, **kwargs):
        location = get_object_or_404(BusinessLocation, pk=pk)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            business_location=location,
        )
        if not created:
            favorite.delete()
            favorited = False
        else:
            favorited = True
        return Response(
            {"favorited": favorited, "business_location_id": location.id},
            status=status.HTTP_200_OK,
        )


# ---- internals -------------------------------------------------------------


def _parse_radius_km(value: str | None) -> float:
    """Default 3km; clamp to [0.1, 50]."""
    try:
        v = float(value) if value not in (None, "") else 3.0
    except (TypeError, ValueError):
        return 3.0
    if v <= 0:
        return 3.0
    return min(v, 50.0)
