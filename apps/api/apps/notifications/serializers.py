"""Serializers for /api/v1/notifications/*."""

from __future__ import annotations

from rest_framework import serializers

from .models import PushPlatform, PushToken


class RegisterPushTokenSerializer(serializers.Serializer):
    """Body for POST /notifications/register-token.

    Idempotent — the view does `update_or_create((user, token))`. The same
    Expo token can move between users (rare, but possible if a device is
    handed off) — in that case the row's `user` updates to the latest
    caller, and the old user no longer receives pushes for that device.
    """

    token = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=PushPlatform.choices)


class PushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushToken
        fields = ("id", "token", "platform", "is_active", "created_at")
        read_only_fields = fields
