"""Views for /users/me."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import MeSerializer, MeUpdateSerializer


class MeView(APIView):
    """GET + PATCH the authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        ser = MeUpdateSerializer(data=request.data, context={"request": request}, partial=True)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response(
            MeSerializer(user, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
