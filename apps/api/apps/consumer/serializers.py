"""Consumer-facing serializers.

Two shapes for bags:
  - BagListSerializer   — lean card payload, no description, no extra images.
  - BagDetailSerializer — extends list w/ description, gallery, hours, reviews preview.

`distance_m` and `is_favorited` are annotations supplied by the view
(see `geo.annotate_distance` and `views.BagListView.get_queryset`). When the
view didn't compute them — e.g. caller has no location, or bag detail
without a viewer — they fall back to `None` / `False` without exploding.
"""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.bags.models import Bag
from apps.businesses.models import BusinessLocation
from apps.reviews.models import Review

from .images import thumb


class BusinessForCardSerializer(serializers.Serializer):
    """Sub-payload embedded in BagListSerializer / BagDetailSerializer.

    Returned as a plain dict (not bound to a model) because we hand-pick
    fields from BusinessLocation + Business + annotated rating aggregates.
    """

    id = serializers.IntegerField()
    location_id = serializers.IntegerField()
    name = serializers.CharField()
    logo_url = serializers.SerializerMethodField()
    address = serializers.CharField()
    latitude = serializers.FloatField(allow_null=True)
    longitude = serializers.FloatField(allow_null=True)
    rating_average = serializers.FloatField(allow_null=True)
    rating_count = serializers.IntegerField()

    def get_logo_url(self, obj) -> str:
        return thumb(obj.get("logo_url") or "", width=120)


def _build_business_payload(location: BusinessLocation) -> dict:
    """Flatten the BusinessLocation + Business + annotated rating fields
    into the shape BusinessForCardSerializer expects.

    Reads from annotations populated upstream by the view's queryset:
        location_rating_avg, location_rating_count.
    """
    business = location.business
    lat = lng = None
    raw_location = getattr(location, "location", None)
    if raw_location is not None:
        # PostGIS Point exposes .y / .x; the JSON shim returns {"lat", "lng"}.
        if hasattr(raw_location, "y"):
            lat, lng = raw_location.y, raw_location.x
        elif isinstance(raw_location, dict):
            lat, lng = raw_location.get("lat"), raw_location.get("lng")

    return {
        "id": business.id,
        "location_id": location.id,
        "name": business.name,
        "logo_url": business.logo_url,
        "address": location.address,
        "latitude": lat,
        "longitude": lng,
        "rating_average": getattr(location, "rating_avg", None),
        "rating_count": getattr(location, "rating_count", 0) or 0,
    }


class BagListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    discount_percent = serializers.IntegerField(read_only=True)
    business = serializers.SerializerMethodField()
    distance_m = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    dietary_tags = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)
    allergen_warnings = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)

    class Meta:
        model = Bag
        fields = (
            "id",
            "title",
            "type",
            "image_url",
            "original_price",
            "sale_price",
            "discount_percent",
            "quantity_available",
            "pickup_window_start",
            "pickup_window_end",
            "business",
            "distance_m",
            "is_favorited",
            "dietary_tags",
            "allergen_warnings",
        )

    def get_image_url(self, obj: Bag) -> str:
        return thumb(obj.image_url, width=600)

    def get_business(self, obj: Bag) -> dict:
        return _build_business_payload(obj.business_location)

    def get_distance_m(self, obj: Bag) -> int | None:
        # The view annotates `distance_m` (in metres) when lat/lng supplied.
        # We tolerate either a float (test shim) or Distance-like object.
        raw = getattr(obj, "distance_m", None)
        if raw is None:
            return None
        if hasattr(raw, "m"):  # GeoDjango Distance object
            return int(raw.m)
        return int(raw)

    def get_is_favorited(self, obj: Bag) -> bool:
        # Annotated by view when authenticated; False otherwise.
        return bool(getattr(obj, "is_favorited", False))


class BagReviewSerializer(serializers.ModelSerializer):
    consumer_first_name = serializers.SerializerMethodField()
    consumer_avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "id",
            "rating",
            "comment",
            "consumer_first_name",
            "consumer_avatar_url",
            "created_at",
        )

    def get_consumer_first_name(self, obj: Review) -> str:
        profile = getattr(obj.consumer, "consumer_profile", None)
        return getattr(profile, "first_name", "") or ""

    def get_consumer_avatar_url(self, obj: Review) -> str:
        profile = getattr(obj.consumer, "consumer_profile", None)
        url = getattr(profile, "avatar_url", "") or ""
        return thumb(url, width=80)


class BagDetailSerializer(BagListSerializer):
    description = serializers.CharField(read_only=True)
    extra_image_urls = serializers.SerializerMethodField()
    business_hours = serializers.SerializerMethodField()
    business_phone = serializers.SerializerMethodField()
    latest_reviews = serializers.SerializerMethodField()

    class Meta(BagListSerializer.Meta):
        fields = (
            *BagListSerializer.Meta.fields,
            "description",
            "extra_image_urls",
            "business_hours",
            "business_phone",
            "latest_reviews",
            "is_active",
            "quantity_total",
        )

    def get_extra_image_urls(self, obj: Bag) -> list[str]:
        return [thumb(u, width=800) for u in (obj.extra_image_urls or [])]

    def get_business_hours(self, obj: Bag) -> dict:
        return obj.business_location.hours_of_operation or {}

    def get_business_phone(self, obj: Bag) -> str:
        return obj.business_location.phone or obj.business_location.business.phone or ""

    def get_latest_reviews(self, obj: Bag) -> list[dict]:
        qs = obj.business_location.reviews.filter(is_visible=True).order_by("-created_at")[:3]
        return BagReviewSerializer(qs, many=True).data


class FavoriteToggleResponseSerializer(serializers.Serializer):
    """Documentation-only — DRF response shape for the toggle endpoint."""

    favorited = serializers.BooleanField()
    business_location_id = serializers.IntegerField()


# ---- coercion utility used by view layer for query params ----------------


def parse_decimal(value: str | None) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(value)
    except (ValueError, ArithmeticError):
        return None


def parse_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
