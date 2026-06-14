"""Admin / sales-rep views for /api/v1/admin/*."""

from __future__ import annotations

from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.businesses.models import Business, BusinessStatus
from apps.users.auth.permissions import AdminOrSalesRepOnly, IsEmailVerified
from apps.users.auth.services.password_reset import issue_reset_links

from .serializers import (
    AdminBusinessDetailSerializer,
    AdminBusinessListSerializer,
    AdminSessionSerializer,
    BusinessReviewActionSerializer,
    CreateDraftBusinessAccountSerializer,
)

ADMIN_PERMISSIONS = [IsAuthenticated, AdminOrSalesRepOnly, IsEmailVerified]


def _notify_business_owner(*, business: Business, subject: str, message: str) -> None:
    recipient = business.owner.email
    if not recipient:
        return
    send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=[recipient],
        fail_silently=True,
    )


class AdminSessionView(APIView):
    permission_classes = ADMIN_PERMISSIONS

    def get(self, request):
        return Response(AdminSessionSerializer(request.user, context={"request": request}).data)


class BusinessListView(APIView):
    permission_classes = ADMIN_PERMISSIONS

    def get(self, request):
        status_filter = request.query_params.get("status", "pending")
        allowed_statuses = {choice for choice, _ in BusinessStatus.choices}
        if status_filter not in allowed_statuses:
            return Response(
                {"detail": "Invalid status filter.", "code": "invalid_status"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = (
            Business.objects.filter(status=status_filter)
            .select_related("owner")
            .order_by("created_at")
        )
        return Response(AdminBusinessListSerializer(qs, many=True).data)


class BusinessDetailView(APIView):
    permission_classes = ADMIN_PERMISSIONS

    def get(self, request, pk: int):
        business = get_object_or_404(
            Business.objects.select_related("owner", "verification").prefetch_related("locations"),
            pk=pk,
        )
        return Response(AdminBusinessDetailSerializer(business).data)


class ApproveBusinessView(APIView):
    permission_classes = ADMIN_PERMISSIONS

    def post(self, request, pk: int):
        business = get_object_or_404(Business, pk=pk)
        business.status = BusinessStatus.APPROVED
        business.rejection_reason = ""
        business.review_notes = ""
        business.approved_by = request.user
        business.approved_at = timezone.now()
        business.save(
            update_fields=[
                "status",
                "rejection_reason",
                "review_notes",
                "approved_by",
                "approved_at",
                "updated_at",
            ]
        )
        _notify_business_owner(
            business=business,
            subject="Tu negocio fue aprobado · La Yapa",
            message=(
                f"Hola, {business.name} fue aprobado en La Yapa.\n"
                "Ya puedes entrar a la app y publicar tus bolsas."
            ),
        )
        return Response(AdminBusinessDetailSerializer(business).data)


class RejectBusinessView(APIView):
    permission_classes = ADMIN_PERMISSIONS

    def post(self, request, pk: int):
        business = get_object_or_404(Business, pk=pk)
        ser = BusinessReviewActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reason = ser.validated_data.get("reason", "").strip()
        if not reason:
            return Response(
                {"detail": "A rejection reason is required.", "code": "missing_reason"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        business.status = BusinessStatus.REJECTED
        business.rejection_reason = reason
        business.review_notes = ""
        business.approved_by = None
        business.approved_at = None
        business.save(
            update_fields=[
                "status",
                "rejection_reason",
                "review_notes",
                "approved_by",
                "approved_at",
                "updated_at",
            ]
        )
        _notify_business_owner(
            business=business,
            subject="Necesitamos ajustes en tu solicitud · La Yapa",
            message=(
                f"Tu solicitud para {business.name} fue rechazada por ahora.\n"
                f"Motivo: {reason}\n"
                "Puedes corregirla y volver a enviarla desde la app."
            ),
        )
        return Response(AdminBusinessDetailSerializer(business).data)


class RequestMoreInfoBusinessView(APIView):
    permission_classes = ADMIN_PERMISSIONS

    def post(self, request, pk: int):
        business = get_object_or_404(Business, pk=pk)
        ser = BusinessReviewActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        notes = ser.validated_data.get("reason", "").strip()
        if not notes:
            return Response(
                {"detail": "Reviewer notes are required.", "code": "missing_reason"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        business.status = BusinessStatus.PENDING
        business.review_notes = notes
        business.rejection_reason = ""
        business.approved_by = None
        business.approved_at = None
        business.save(
            update_fields=[
                "status",
                "review_notes",
                "rejection_reason",
                "approved_by",
                "approved_at",
                "updated_at",
            ]
        )
        _notify_business_owner(
            business=business,
            subject="Necesitamos más información · La Yapa",
            message=(
                f"Tu solicitud para {business.name} sigue en revisión.\n"
                f"Notas del equipo: {notes}\n"
                "Actualiza tu información y vuelve a enviar la solicitud desde la app."
            ),
        )
        return Response(AdminBusinessDetailSerializer(business).data)


class CreateDraftBusinessAccountView(APIView):
    permission_classes = ADMIN_PERMISSIONS

    def post(self, request):
        ser = CreateDraftBusinessAccountSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        business = ser.save()
        return Response(
            AdminBusinessDetailSerializer(business).data, status=status.HTTP_201_CREATED
        )


class SendBusinessSetupLinkView(APIView):
    permission_classes = ADMIN_PERMISSIONS

    def post(self, request, pk: int):
        business = get_object_or_404(Business.objects.select_related("owner"), pk=pk)
        web_link, _ = issue_reset_links(business.owner)
        send_mail(
            subject="Configura tu contraseña · La Yapa",
            message=(
                f"Hola,\n\n"
                f"Tu cuenta para administrar {business.name} ya está lista.\n"
                f"Configura tu contraseña aquí: {web_link}\n\n"
                "Si no esperabas este correo, puedes ignorarlo."
            ),
            from_email=None,
            recipient_list=[business.owner.email],
            fail_silently=True,
        )
        return Response(
            {"sent": True, "business_id": business.id, "owner_email": business.owner.email}
        )
