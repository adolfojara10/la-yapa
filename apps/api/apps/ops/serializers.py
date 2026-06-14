"""Serializers for /api/v1/admin/*."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.businesses.models import (
    Business,
    BusinessLocation,
    BusinessStatus,
    BusinessTier,
    BusinessType,
    BusinessVerification,
    PayoutFrequency,
    PayoutMethod,
)
from apps.geo.utils import make_point
from apps.users.api.serializers import MeSerializer
from apps.users.models import User


class AdminSessionSerializer(MeSerializer):
    pass


class AdminBusinessListSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    has_locations = serializers.BooleanField(read_only=True)

    class Meta:
        model = Business
        fields = (
            "id",
            "name",
            "business_type",
            "tier",
            "status",
            "owner_email",
            "created_at",
            "has_locations",
        )
        read_only_fields = fields


class AdminBusinessLocationSerializer(serializers.ModelSerializer):
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
        raw = obj.location
        if raw is None:
            return None
        if hasattr(raw, "y"):
            return raw.y
        if isinstance(raw, dict):
            return raw.get("lat")
        return None

    def get_lng(self, obj: BusinessLocation):
        raw = obj.location
        if raw is None:
            return None
        if hasattr(raw, "x"):
            return raw.x
        if isinstance(raw, dict):
            return raw.get("lng")
        return None


class AdminBusinessVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessVerification
        fields = (
            "ruc_number",
            "ruc_document_url",
            "cedula_number",
            "cedula_document_url",
            "selfie_with_cedula_url",
            "permiso_funcionamiento_url",
            "arcsa_url",
            "bank_proof_url",
            "business_photo_url",
            "food_safety_terms_accepted_at",
        )
        read_only_fields = fields


class AdminBusinessDetailSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    owner_phone = serializers.CharField(source="owner.phone", read_only=True)
    locations = AdminBusinessLocationSerializer(many=True, read_only=True)
    verification = AdminBusinessVerificationSerializer(read_only=True)

    class Meta:
        model = Business
        fields = (
            "id",
            "name",
            "business_type",
            "tier",
            "description",
            "phone",
            "email",
            "website",
            "status",
            "rejection_reason",
            "review_notes",
            "owner_email",
            "owner_phone",
            "payout_frequency",
            "payout_method",
            "created_at",
            "approved_at",
            "locations",
            "verification",
        )
        read_only_fields = fields


class BusinessReviewActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class CreateDraftBusinessAccountSerializer(serializers.Serializer):
    owner_email = serializers.EmailField()
    owner_phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    business_name = serializers.CharField(max_length=140)
    business_type = serializers.ChoiceField(choices=BusinessType.choices)
    tier = serializers.ChoiceField(choices=BusinessTier.choices, default=BusinessTier.FORMAL)
    description = serializers.CharField(required=False, allow_blank=True)
    business_phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    business_email = serializers.EmailField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    payout_frequency = serializers.ChoiceField(
        choices=PayoutFrequency.choices,
        default=PayoutFrequency.WEEKLY,
        required=False,
    )
    payout_method = serializers.ChoiceField(
        choices=PayoutMethod.choices,
        default=PayoutMethod.BANK_TRANSFER,
        required=False,
    )
    location_name = serializers.CharField(required=False, allow_blank=True, max_length=140)
    address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    lat = serializers.FloatField(required=False)
    lng = serializers.FloatField(required=False)

    def validate_owner_email(self, value: str) -> str:
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email

    def validate(self, attrs: dict) -> dict:
        if bool(attrs.get("lat")) != bool(attrs.get("lng")):
            raise serializers.ValidationError("lat and lng must be supplied together.")
        return attrs

    @transaction.atomic
    def save(self, **kwargs) -> Business:
        actor: User = self.context["request"].user
        email = self.validated_data["owner_email"]
        username_base = email.split("@", 1)[0][:140] or "business-owner"
        username = username_base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{username_base}-{counter}"
            counter += 1

        owner = User.objects.create(
            email=email,
            username=username,
            role=User.Role.BUSINESS_OWNER,
            phone=self.validated_data.get("owner_phone", ""),
            is_email_verified=True,
            email_verified_at=timezone.now(),
        )
        owner.set_unusable_password()
        owner.save(update_fields=["password", "updated_at"])

        business = Business.objects.create(
            owner=owner,
            name=self.validated_data["business_name"],
            business_type=self.validated_data["business_type"],
            tier=self.validated_data["tier"],
            description=self.validated_data.get("description", ""),
            phone=self.validated_data.get("business_phone", ""),
            email=self.validated_data.get("business_email", ""),
            website=self.validated_data.get("website", ""),
            status=BusinessStatus.PENDING,
            payout_frequency=self.validated_data.get("payout_frequency", PayoutFrequency.WEEKLY),
            payout_method=self.validated_data.get("payout_method", PayoutMethod.BANK_TRANSFER),
            review_notes=f"Draft business created by {actor.email}",
        )

        location_name = self.validated_data.get("location_name", "").strip()
        address = self.validated_data.get("address", "").strip()
        if location_name or address:
            BusinessLocation.objects.create(
                business=business,
                name=location_name or "Local principal",
                address=address or "Pendiente",
                location=(
                    make_point(self.validated_data["lat"], self.validated_data["lng"])
                    if "lat" in self.validated_data and "lng" in self.validated_data
                    else None
                ),
            )

        return business
