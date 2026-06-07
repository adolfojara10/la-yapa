"""Serializers for /api/v1/business/*.

Privacy-first: consumer payload is limited to first name + dietary tags
attached to the BAG (not the consumer's profile preferences). No email,
phone, last name, or other PII leaks to vendors.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.bags.models import Bag
from apps.consumer.images import thumb
from apps.orders.models import Order
from apps.suspended_meals.models import SuspendedMealDonation


class _BagSnapshotForBusiness(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    image_url = serializers.SerializerMethodField()
    type = serializers.CharField()
    pickup_window_start = serializers.DateTimeField()
    pickup_window_end = serializers.DateTimeField()
    dietary_tags = serializers.SerializerMethodField()
    allergen_warnings = serializers.SerializerMethodField()

    def get_image_url(self, obj: Bag) -> str:
        return thumb(obj.image_url, width=400)

    def get_dietary_tags(self, obj: Bag) -> list[str]:
        return list(obj.dietary_tags.values_list("name", flat=True))

    def get_allergen_warnings(self, obj: Bag) -> list[str]:
        return list(obj.allergen_warnings.values_list("name", flat=True))


class BusinessOrderSerializer(serializers.ModelSerializer):
    """Shape returned by the business-facing list + detail endpoints.

    Includes:
      - Order status + quantity + total
      - Pickup code (vendor needs to verify against what the consumer shows)
      - Consumer first name ONLY (privacy)
      - Bag snapshot with dietary tags + allergen warnings
      - PIN-lock state (lets the mobile UI hide PIN entry when locked)
      - Pickup window helpers (so the UI can render "open in N min")
    """

    bag = serializers.SerializerMethodField()
    consumer_first_name = serializers.SerializerMethodField()
    business_location_id = serializers.IntegerField(read_only=True)
    business_location_name = serializers.SerializerMethodField()
    is_within_pickup_window = serializers.SerializerMethodField()
    is_pin_locked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "quantity",
            "sale_price_snapshot",
            "total_paid",
            "pickup_code",
            "payment_method",
            "donate_as_suspended_meal",
            "picked_up_at",
            "created_at",
            "consumer_first_name",
            "business_location_id",
            "business_location_name",
            "bag",
            "is_within_pickup_window",
            "is_pin_locked",
        )
        read_only_fields = fields

    def get_bag(self, obj: Order) -> dict:
        return _BagSnapshotForBusiness(obj.bag).data

    def get_consumer_first_name(self, obj: Order) -> str:
        profile = getattr(obj.consumer, "consumer_profile", None)
        return getattr(profile, "first_name", "") or "Cliente"

    def get_business_location_name(self, obj: Order) -> str:
        return obj.business_location.name

    def get_is_within_pickup_window(self, obj: Order) -> bool:
        return obj.is_within_pickup_window()


# ----- pickup confirm request bodies ---------------------------------------


class ConfirmPickupByIdSerializer(serializers.Serializer):
    """For POST /business/orders/{id}/confirm-pickup. EXACTLY one of
    qr_token / pin must be supplied."""

    qr_token = serializers.UUIDField(required=False)
    pin = serializers.CharField(required=False, min_length=4, max_length=4)

    def validate(self, attrs: dict) -> dict:
        if bool(attrs.get("qr_token")) == bool(attrs.get("pin")):
            raise serializers.ValidationError("Provide exactly one of qr_token or pin.")
        return attrs


class ConfirmPickupByScanSerializer(serializers.Serializer):
    """For POST /business/orders/confirm-pickup-by-scan — QR-only path
    used by the scanner screen (which doesn't know the order id)."""

    qr_token = serializers.UUIDField()


class ConfirmPickupByPinSerializer(serializers.Serializer):
    """For POST /business/orders/confirm-pickup-by-pin — PIN-only path
    used by the dashboard's manual entry sheet."""

    business_location_id = serializers.IntegerField()
    pin = serializers.CharField(min_length=4, max_length=4)


# ----- suspended meals -----------------------------------------------------


class SuspendedMealForDispatchSerializer(serializers.ModelSerializer):
    """Shape returned by /business/suspended-meals/active."""

    bag_title = serializers.SerializerMethodField()
    business_location_id = serializers.SerializerMethodField()
    business_location_name = serializers.SerializerMethodField()

    class Meta:
        model = SuspendedMealDonation
        fields = (
            "id",
            "amount",
            "is_anonymous",
            "created_at",
            "bag_title",
            "business_location_id",
            "business_location_name",
        )
        read_only_fields = fields

    def get_bag_title(self, obj: SuspendedMealDonation) -> str:
        return obj.bag.title if obj.bag else ""

    def get_business_location_id(self, obj: SuspendedMealDonation) -> int | None:
        return obj.bag.business_location_id if obj.bag else None

    def get_business_location_name(self, obj: SuspendedMealDonation) -> str:
        return obj.bag.business_location.name if obj.bag else "Pool general"


class DispatchSuspendedSerializer(serializers.Serializer):
    """Body for POST /business/suspended-meals/dispatch."""

    donation_id = serializers.UUIDField()
    business_location_id = serializers.IntegerField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)


# ----- dashboard ----------------------------------------------------------


class DashboardSummarySerializer(serializers.Serializer):
    """Shape returned by /business/dashboard."""

    active_orders_count = serializers.IntegerField()
    today_completed_count = serializers.IntegerField()
    suspended_meals_available = serializers.IntegerField()
