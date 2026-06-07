"""Notifications endpoints."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PushToken
from .serializers import PushTokenSerializer, RegisterPushTokenSerializer


class RegisterPushTokenView(APIView):
    """POST /api/v1/notifications/register-token

    Idempotent device-token registration. Mobile calls this once per
    cold start after auth hydrates.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = RegisterPushTokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        token = ser.validated_data["token"]
        platform = ser.validated_data["platform"]
        # update_or_create on `token` (unique). If the same token was
        # previously associated with another user, ownership transfers
        # to the current request.
        instance, _ = PushToken.objects.update_or_create(
            token=token,
            defaults={
                "user": request.user,
                "platform": platform,
                "is_active": True,
            },
        )
        return Response(PushTokenSerializer(instance).data, status=status.HTTP_200_OK)
