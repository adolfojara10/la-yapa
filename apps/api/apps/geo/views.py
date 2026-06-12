"""Public geo proxy endpoints backed by a configurable OSM-compatible provider."""

from __future__ import annotations

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import GeoProviderError, reverse_geocode, search_places


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(max_length=160)
    country = serializers.CharField(max_length=2, required=False, default="ec")
    limit = serializers.IntegerField(min_value=1, max_value=10, required=False, default=5)
    lat = serializers.FloatField(required=False)
    lng = serializers.FloatField(required=False)
    lang = serializers.CharField(max_length=10, required=False, allow_blank=True)


class ReverseQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    lang = serializers.CharField(max_length=10, required=False, allow_blank=True)


class GeoSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key="ip", rate="30/m", block=True))
    def get(self, request):
        serializer = SearchQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        payload = dict(serializer.validated_data)
        payload["query"] = payload.pop("q")
        try:
            results = search_places(**payload)
        except GeoProviderError:
            return Response(
                {"detail": "Geo provider unavailable", "code": "geo_provider_unavailable"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"results": results}, status=status.HTTP_200_OK)


class GeoReverseView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(ratelimit(key="ip", rate="60/m", block=True))
    def get(self, request):
        serializer = ReverseQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            result = reverse_geocode(**serializer.validated_data)
        except GeoProviderError:
            return Response(
                {"detail": "Geo provider unavailable", "code": "geo_provider_unavailable"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"result": result}, status=status.HTTP_200_OK)
