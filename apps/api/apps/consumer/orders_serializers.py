"""Serializers for /api/v1/consumer/orders."""

from __future__ import annotations

from rest_framework import serializers

from apps.bags.models import Bag
from apps.orders.models import Order
from apps.payments.models import BonusCredit

from .images import thumb


class _OrderBagSnapshotSerializer(serializers.Serializer):
    """Lean snapshot of the bag at order time. We pull live fields from Bag
    for image/title (so a bag rename propagates), but keep snapshot prices
    on the Order for accounting honesty."""

    id = serializers.UUIDField()
    title = serializers.CharField()
    image_url = serializers.SerializerMethodField()
    type = serializers.CharField()

    def get_image_url(self, obj: Bag) -> str:
        return thumb(obj.image_url, width=400)


class _OrderLocationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    business_name = serializers.CharField()
    name = serializers.CharField()
    address = serializers.CharField()
    phone = serializers.CharField()
    latitude = serializers.FloatField(allow_null=True)
    longitude = serializers.FloatField(allow_null=True)


class OrderSerializer(serializers.ModelSerializer):
    bag = serializers.SerializerMethodField()
    business_location = serializers.SerializerMethodField()
    is_within_consumer_cancel_window = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "status",
            "quantity",
            "original_price_snapshot",
            "sale_price_snapshot",
            "applied_credit_amount",
            "total_paid",
            "pickup_code",
            "pickup_qr_token",
            "payment_method",
            "donate_as_suspended_meal",
            "cancelled_by",
            "cancelled_at",
            "cancellation_reason",
            "picked_up_at",
            "created_at",
            "updated_at",
            "bag",
            "business_location",
            "is_within_consumer_cancel_window",
        )
        read_only_fields = fields

    def get_bag(self, obj: Order) -> dict:
        return _OrderBagSnapshotSerializer(obj.bag).data | {
            "pickup_window_start": obj.bag.pickup_window_start.isoformat(),
            "pickup_window_end": obj.bag.pickup_window_end.isoformat(),
        }

    def get_business_location(self, obj: Order) -> dict:
        loc = obj.business_location
        lat = lng = None
        raw = getattr(loc, "location", None)
        if raw is not None:
            if hasattr(raw, "y"):
                lat, lng = raw.y, raw.x
            elif isinstance(raw, dict):
                lat, lng = raw.get("lat"), raw.get("lng")
        return {
            "id": loc.id,
            "business_name": loc.business.name,
            "name": loc.name,
            "address": loc.address,
            "phone": loc.phone or loc.business.phone or "",
            "latitude": lat,
            "longitude": lng,
        }

    def get_is_within_consumer_cancel_window(self, obj: Order) -> bool:
        return obj.is_within_consumer_cancel_window()


class CreateOrderSerializer(serializers.Serializer):
    bag_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=10, default=1)
    donate_as_suspended_meal = serializers.BooleanField(default=False)


class CancelOrderSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class RedeemCreditSerializer(serializers.Serializer):
    credit_id = serializers.IntegerField()


class BonusCreditSerializer(serializers.ModelSerializer):
    is_available = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = BonusCredit
        fields = (
            "id",
            "amount",
            "source",
            "expires_at",
            "redeemed_at",
            "notes",
            "is_available",
            "is_expired",
        )
        read_only_fields = fields
