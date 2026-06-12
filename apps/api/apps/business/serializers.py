"""Serializers for /api/v1/business/*.

Privacy-first: consumer payload is limited to first name + dietary tags
attached to the BAG (not the consumer's profile preferences). No email,
phone, last name, or other PII leaks to vendors.
"""

from __future__ import annotations

import json
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.bags.models import AllergenTag, Bag, BagTemplate
from apps.business.services import bag_has_sales
from apps.businesses.models import (
    Business,
    BusinessLocation,
    BusinessTier,
    BusinessType,
    PayoutFrequency,
    PayoutMethod,
)
from apps.consumer.images import thumb
from apps.orders.models import Order
from apps.suspended_meals.models import SuspendedMealDonation
from apps.users.models import DietaryTag


def _point_payload(location) -> dict[str, float | None]:
    raw = getattr(location, "location", None)
    if raw is None:
        return {"lat": None, "lng": None}
    if hasattr(raw, "y"):
        return {"lat": raw.y, "lng": raw.x}
    if isinstance(raw, dict):
        return {"lat": raw.get("lat"), "lng": raw.get("lng")}
    return {"lat": None, "lng": None}


class JSONStringListField(serializers.ListField):
    def to_internal_value(self, data):
        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], str):
            stripped = data[0].strip()
            if stripped.startswith("["):
                data = [] if not stripped else json.loads(stripped)
        if isinstance(data, str):
            stripped = data.strip()
            data = [] if not stripped else json.loads(stripped)
        return super().to_internal_value(data)


class JSONStringDictField(serializers.JSONField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            stripped = data.strip()
            data = {} if not stripped else json.loads(stripped)
        return super().to_internal_value(data)


class BusinessAccountSerializer(serializers.ModelSerializer):
    has_locations = serializers.BooleanField(read_only=True)

    class Meta:
        model = Business
        fields = (
            "id",
            "name",
            "business_type",
            "tier",
            "status",
            "rejection_reason",
            "payout_method",
            "has_locations",
        )
        read_only_fields = fields


class BusinessOnboardingSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=140)
    business_type = serializers.ChoiceField(choices=BusinessType.choices)
    tier = serializers.ChoiceField(choices=BusinessTier.choices)
    description = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)

    location_name = serializers.CharField(max_length=140)
    address = serializers.CharField(max_length=255)
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    location_phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    hours_of_operation = JSONStringDictField(required=False)

    payout_frequency = serializers.ChoiceField(
        choices=PayoutFrequency.choices,
        default=PayoutFrequency.WEEKLY,
        required=False,
    )
    payout_method = serializers.ChoiceField(choices=PayoutMethod.choices)
    account_holder = serializers.CharField(max_length=140)
    bank_name = serializers.CharField(required=False, allow_blank=True, max_length=140)
    account_number = serializers.CharField(required=False, allow_blank=True, max_length=80)
    account_type = serializers.CharField(required=False, allow_blank=True, max_length=40)
    deuna_phone = serializers.CharField(required=False, allow_blank=True, max_length=20)

    cedula_number = serializers.CharField(max_length=20)
    ruc_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    has_food_handling = serializers.BooleanField(default=True, required=False)
    food_safety_terms_accepted = serializers.BooleanField()

    ruc_document = serializers.FileField(required=False)
    cedula_document = serializers.FileField(required=False)
    selfie_with_cedula = serializers.FileField(required=False)
    permiso_funcionamiento = serializers.FileField(required=False)
    arcsa_document = serializers.FileField(required=False)
    bank_proof = serializers.FileField(required=False)
    business_photo = serializers.FileField(required=False)

    def validate_hours_of_operation(self, value: dict) -> dict:
        if not isinstance(value, dict):
            raise serializers.ValidationError("Expected an object keyed by weekday.")
        return value

    def validate(self, attrs: dict) -> dict:
        tier = attrs["tier"]
        if not attrs.get("food_safety_terms_accepted"):
            raise serializers.ValidationError(
                {"food_safety_terms_accepted": "Food safety terms must be accepted."}
            )

        if attrs["payout_method"] == PayoutMethod.BANK_TRANSFER:
            required_bank_fields = ("bank_name", "account_number")
            missing = [field for field in required_bank_fields if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError(
                    {
                        field: "This field is required for bank transfer payouts."
                        for field in missing
                    }
                )
        elif not attrs.get("deuna_phone"):
            raise serializers.ValidationError(
                {"deuna_phone": "This field is required for DeUna payouts."}
            )

        if tier == BusinessTier.FORMAL:
            for field in (
                "ruc_number",
                "ruc_document",
                "cedula_document",
                "permiso_funcionamiento",
                "bank_proof",
            ):
                if not attrs.get(field):
                    raise serializers.ValidationError({field: "This field is required."})
            if attrs.get("has_food_handling") and not attrs.get("arcsa_document"):
                raise serializers.ValidationError(
                    {"arcsa_document": "ARCSA document is required for food businesses."}
                )
        else:
            for field in ("cedula_document", "selfie_with_cedula", "business_photo"):
                if not attrs.get(field):
                    raise serializers.ValidationError({field: "This field is required."})

        return attrs


class BusinessLocationSerializer(serializers.ModelSerializer):
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()

    class Meta:
        model = BusinessLocation
        fields = (
            "id",
            "name",
            "address",
            "lat",
            "lng",
            "phone",
            "is_active",
            "hours_of_operation",
        )
        read_only_fields = fields

    def get_lat(self, obj: BusinessLocation):
        return _point_payload(obj)["lat"]

    def get_lng(self, obj: BusinessLocation):
        return _point_payload(obj)["lng"]


class BusinessLocationWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=140)
    address = serializers.CharField(max_length=255)
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    is_active = serializers.BooleanField(required=False)
    hours_of_operation = JSONStringDictField(required=False)

    def validate_hours_of_operation(self, value: dict) -> dict:
        if not isinstance(value, dict):
            raise serializers.ValidationError("Expected an object keyed by weekday.")
        return value


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


class ManagedBagSerializer(serializers.ModelSerializer):
    business_location_name = serializers.CharField(source="business_location.name", read_only=True)
    dietary_tags = serializers.SerializerMethodField()
    allergen_warnings = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    quantity_sold = serializers.SerializerMethodField()

    class Meta:
        model = Bag
        fields = (
            "id",
            "business_location_id",
            "business_location_name",
            "type",
            "title",
            "description",
            "image_url",
            "original_price",
            "sale_price",
            "quantity_available",
            "quantity_total",
            "quantity_sold",
            "pickup_window_start",
            "pickup_window_end",
            "dietary_tags",
            "allergen_warnings",
            "is_active",
            "is_suspended_meal_eligible",
            "can_edit",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_dietary_tags(self, obj: Bag) -> list[str]:
        return list(obj.dietary_tags.values_list("name", flat=True))

    def get_allergen_warnings(self, obj: Bag) -> list[str]:
        return list(obj.allergen_warnings.values_list("name", flat=True))

    def get_can_edit(self, obj: Bag) -> bool:
        return not bag_has_sales(obj)

    def get_quantity_sold(self, obj: Bag) -> int:
        return max((obj.quantity_total or 0) - (obj.quantity_available or 0), 0)


class BagWriteSerializer(serializers.Serializer):
    business_location_id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=Bag._meta.get_field("type").choices)
    title = serializers.CharField(max_length=140)
    description = serializers.CharField(required=False, allow_blank=True)
    image = serializers.FileField(required=False)
    original_price = serializers.DecimalField(max_digits=8, decimal_places=2)
    sale_price = serializers.DecimalField(max_digits=8, decimal_places=2)
    quantity_available = serializers.IntegerField(min_value=1)
    pickup_window_start = serializers.DateTimeField()
    pickup_window_end = serializers.DateTimeField()
    dietary_tags = JSONStringListField(
        child=serializers.SlugRelatedField(slug_field="name", queryset=DietaryTag.objects.all()),
        required=False,
    )
    allergen_warnings = JSONStringListField(
        child=serializers.SlugRelatedField(slug_field="name", queryset=AllergenTag.objects.all()),
        required=False,
    )
    is_suspended_meal_eligible = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)

    def validate(self, attrs: dict) -> dict:
        instance = getattr(self, "instance", None)
        start = attrs.get("pickup_window_start", getattr(instance, "pickup_window_start", None))
        end = attrs.get("pickup_window_end", getattr(instance, "pickup_window_end", None))
        if start is None or end is None:
            raise serializers.ValidationError("Pickup window is required.")
        if end <= start:
            raise serializers.ValidationError(
                {"pickup_window_end": "Pickup window end must be after the start."}
            )
        if start <= timezone.now():
            raise serializers.ValidationError(
                {"pickup_window_start": "Pickup window must be in the future."}
            )
        original_price = attrs.get("original_price", getattr(instance, "original_price", None))
        sale_price = attrs.get("sale_price", getattr(instance, "sale_price", None))
        if original_price is None or sale_price is None:
            raise serializers.ValidationError("Original and sale prices are required.")
        max_allowed = (original_price * Decimal("0.5")).quantize(Decimal("0.01"))
        if sale_price > max_allowed:
            raise serializers.ValidationError(
                {"sale_price": f"Sale price must be at most {max_allowed}."}
            )
        if sale_price < Decimal("1.50"):
            raise serializers.ValidationError({"sale_price": "Sale price must be at least 1.50."})
        return attrs


class BagDuplicateSerializer(serializers.Serializer):
    business_location_id = serializers.IntegerField(required=False)
    quantity_available = serializers.IntegerField(required=False, min_value=1)
    pickup_window_start = serializers.DateTimeField(required=False)
    pickup_window_end = serializers.DateTimeField(required=False)

    def validate(self, attrs: dict) -> dict:
        start = attrs.get("pickup_window_start")
        end = attrs.get("pickup_window_end")
        if bool(start) != bool(end):
            raise serializers.ValidationError(
                "pickup_window_start and pickup_window_end must be supplied together."
            )
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"pickup_window_end": "Pickup window end must be after the start."}
            )
        if start and start <= timezone.now():
            raise serializers.ValidationError(
                {"pickup_window_start": "Pickup window must be in the future."}
            )
        return attrs


class BagTemplateSerializer(serializers.ModelSerializer):
    dietary_tags = serializers.SerializerMethodField()
    allergen_warnings = serializers.SerializerMethodField()

    class Meta:
        model = BagTemplate
        fields = (
            "id",
            "name",
            "type",
            "title",
            "description",
            "image_url",
            "original_price",
            "sale_price",
            "dietary_tags",
            "allergen_warnings",
            "is_suspended_meal_eligible",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_dietary_tags(self, obj: BagTemplate) -> list[str]:
        return list(obj.dietary_tags.values_list("name", flat=True))

    def get_allergen_warnings(self, obj: BagTemplate) -> list[str]:
        return list(obj.allergen_warnings.values_list("name", flat=True))


class BagTemplateWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=140)
    type = serializers.ChoiceField(choices=Bag._meta.get_field("type").choices)
    title = serializers.CharField(max_length=140)
    description = serializers.CharField(required=False, allow_blank=True)
    image = serializers.FileField(required=False)
    original_price = serializers.DecimalField(max_digits=8, decimal_places=2)
    sale_price = serializers.DecimalField(max_digits=8, decimal_places=2)
    dietary_tags = JSONStringListField(
        child=serializers.SlugRelatedField(slug_field="name", queryset=DietaryTag.objects.all()),
        required=False,
    )
    allergen_warnings = JSONStringListField(
        child=serializers.SlugRelatedField(slug_field="name", queryset=AllergenTag.objects.all()),
        required=False,
    )
    is_suspended_meal_eligible = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs: dict) -> dict:
        original_price = attrs["original_price"]
        sale_price = attrs["sale_price"]
        max_allowed = (original_price * Decimal("0.5")).quantize(Decimal("0.01"))
        if sale_price > max_allowed:
            raise serializers.ValidationError(
                {"sale_price": f"Sale price must be at most {max_allowed}."}
            )
        if sale_price < Decimal("1.50"):
            raise serializers.ValidationError({"sale_price": "Sale price must be at least 1.50."})
        return attrs


class ConfirmPickupByIdSerializer(serializers.Serializer):
    qr_token = serializers.UUIDField(required=False)
    pin = serializers.CharField(required=False, min_length=4, max_length=4)

    def validate(self, attrs: dict) -> dict:
        if bool(attrs.get("qr_token")) == bool(attrs.get("pin")):
            raise serializers.ValidationError("Provide exactly one of qr_token or pin.")
        return attrs


class ConfirmPickupByScanSerializer(serializers.Serializer):
    qr_token = serializers.UUIDField()


class ConfirmPickupByPinSerializer(serializers.Serializer):
    business_location_id = serializers.IntegerField()
    pin = serializers.CharField(min_length=4, max_length=4)


class SuspendedMealForDispatchSerializer(serializers.ModelSerializer):
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
    donation_id = serializers.UUIDField()
    business_location_id = serializers.IntegerField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)


class DashboardSummarySerializer(serializers.Serializer):
    active_orders_count = serializers.IntegerField()
    today_completed_count = serializers.IntegerField()
    suspended_meals_available = serializers.IntegerField()
    today_orders_count = serializers.IntegerField()
    today_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    today_bags_sold = serializers.IntegerField()
