"""Serializers for /users/me."""

from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from apps.businesses.models import Business
from apps.users.models import ConsumerProfile, DietaryTag, User


class _PointFieldSerializer(serializers.Serializer):
    """Tiny lat/lng serializer that mirrors the PointField shim."""

    lat = serializers.FloatField()
    lng = serializers.FloatField()


class ConsumerProfileSerializer(serializers.ModelSerializer):
    dietary_preferences = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=DietaryTag.objects.all(),
        required=False,
    )
    onboarding_completed = serializers.BooleanField(read_only=True)
    default_location = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = ConsumerProfile
        fields = (
            "first_name",
            "last_name",
            "avatar_url",
            "default_location",
            "default_address",
            "dietary_preferences",
            "referral_code",
            "onboarding_completed",
        )
        read_only_fields = ("referral_code", "onboarding_completed")


class BusinessSummarySerializer(serializers.ModelSerializer):
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


class MeSerializer(serializers.ModelSerializer):
    consumer_profile = ConsumerProfileSerializer(read_only=True)
    onboarding_completed = serializers.SerializerMethodField()
    business_summary = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "role",
            "language",
            "phone",
            "is_email_verified",
            "email_verified_at",
            "is_premium",
            "premium_expires_at",
            "consumer_profile",
            "business_summary",
            "onboarding_completed",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "email",
            "role",
            "is_email_verified",
            "email_verified_at",
            "is_premium",
            "premium_expires_at",
            "consumer_profile",
            "business_summary",
            "onboarding_completed",
            "created_at",
            "updated_at",
        )

    def get_onboarding_completed(self, obj: User) -> bool:
        if obj.role == User.Role.BUSINESS_OWNER:
            return self._primary_business(obj) is not None
        if obj.role != User.Role.CONSUMER:
            return True
        profile = getattr(obj, "consumer_profile", None)
        return bool(profile and profile.onboarding_completed)

    def get_business_summary(self, obj: User) -> dict | None:
        if obj.role != User.Role.BUSINESS_OWNER:
            return None
        business = self._primary_business(obj)
        if business is None:
            return None
        return BusinessSummarySerializer(business).data

    def _primary_business(self, obj: User) -> Business | None:
        return obj.businesses.order_by("created_at").first()


class MeUpdateSerializer(serializers.Serializer):
    """Partial-update surface for the authed user. Spans User + ConsumerProfile
    in a single atomic transaction."""

    # User-level fields
    language = serializers.ChoiceField(choices=User.Language.choices, required=False)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)

    # ConsumerProfile fields (consumer role only)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=80)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=80)
    default_address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    default_location = serializers.JSONField(required=False, allow_null=True)
    dietary_preferences = serializers.SlugRelatedField(
        slug_field="name",
        many=True,
        queryset=DietaryTag.objects.all(),
        required=False,
    )
    avatar_url = serializers.URLField(required=False, allow_blank=True)

    def validate_default_location(self, value):
        if value in (None, ""):
            return None
        if not isinstance(value, dict) or "lat" not in value or "lng" not in value:
            raise serializers.ValidationError("Expected {'lat': float, 'lng': float}.")
        return value

    @transaction.atomic
    def save(self, **kwargs) -> User:
        user: User = self.context["request"].user
        user_fields = {}
        for f in ("language", "phone"):
            if f in self.validated_data:
                user_fields[f] = self.validated_data[f]
        if user_fields:
            for k, v in user_fields.items():
                setattr(user, k, v)
            user.save(update_fields=[*user_fields.keys(), "updated_at"])

        if user.role == User.Role.CONSUMER:
            profile, _ = ConsumerProfile.objects.get_or_create(user=user)
            profile_fields = {}
            for f in (
                "first_name",
                "last_name",
                "default_address",
                "default_location",
                "avatar_url",
            ):
                if f in self.validated_data:
                    profile_fields[f] = self.validated_data[f]
            if profile_fields:
                for k, v in profile_fields.items():
                    setattr(profile, k, v)
                profile.save(update_fields=[*profile_fields.keys(), "updated_at"])
            if "dietary_preferences" in self.validated_data:
                profile.dietary_preferences.set(self.validated_data["dietary_preferences"])

        return user
