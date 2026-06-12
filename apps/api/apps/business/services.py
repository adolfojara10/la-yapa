"""Write-side helpers for /api/v1/business/*."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta

from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from apps.bags.models import Bag
from apps.businesses.models import (
    Business,
    BusinessLocation,
    BusinessStatus,
    BusinessTier,
    BusinessVerification,
)
from apps.core.uploads import store_uploaded_file
from apps.geo.utils import make_point
from apps.orders.models import Order, OrderStatus
from apps.users.models import User


class BusinessServiceError(Exception):
    code = "business_service_error"

    def __init__(self, message: str = "", code: str | None = None):
        super().__init__(message or self.code)
        if code:
            self.code = code


class OnboardingAlreadyApproved(BusinessServiceError):
    code = "business_already_approved"


class BagEditNotAllowed(BusinessServiceError):
    code = "bag_edit_not_allowed"


@dataclass
class UploadedVerificationFiles:
    ruc_document_url: str = ""
    cedula_document_url: str = ""
    selfie_with_cedula_url: str = ""
    permiso_funcionamiento_url: str = ""
    arcsa_url: str = ""
    bank_proof_url: str = ""
    business_photo_url: str = ""


def primary_business_for_owner(user) -> Business | None:
    return user.businesses.order_by("created_at").first()


def owned_locations_qs(user):
    return BusinessLocation.objects.filter(business__owner=user)


@transaction.atomic
def submit_onboarding(*, user, payload: dict, files: dict) -> Business:
    business = primary_business_for_owner(user)
    if business is not None and business.status == BusinessStatus.APPROVED:
        raise OnboardingAlreadyApproved("Your business is already approved.")

    uploaded = _store_verification_files(files=files, tier=payload["tier"])
    bank_account = _build_bank_account(payload)
    now = timezone.now()

    business_defaults = {
        "name": payload["name"],
        "business_type": payload["business_type"],
        "tier": payload["tier"],
        "description": payload.get("description", ""),
        "phone": payload.get("phone", ""),
        "email": payload.get("email", ""),
        "website": payload.get("website", ""),
        "status": BusinessStatus.PENDING,
        "rejection_reason": "",
        "approved_at": None,
        "approved_by": None,
        "payout_frequency": payload.get("payout_frequency"),
        "payout_method": payload["payout_method"],
        "bank_account": json.dumps(bank_account),
    }
    if business is None:
        business = Business.objects.create(owner=user, **business_defaults)
    else:
        for field, value in business_defaults.items():
            setattr(business, field, value)
        business.save()

    BusinessVerification.objects.update_or_create(
        business=business,
        defaults={
            "ruc_number": payload.get("ruc_number", ""),
            "ruc_document_url": uploaded.ruc_document_url,
            "cedula_number": payload["cedula_number"],
            "cedula_document_url": uploaded.cedula_document_url,
            "selfie_with_cedula_url": uploaded.selfie_with_cedula_url,
            "permiso_funcionamiento_url": uploaded.permiso_funcionamiento_url,
            "arcsa_url": uploaded.arcsa_url,
            "bank_proof_url": uploaded.bank_proof_url,
            "business_photo_url": uploaded.business_photo_url,
            "food_safety_terms_accepted_at": now,
        },
    )

    location_defaults = {
        "name": payload["location_name"],
        "address": payload["address"],
        "location": make_point(payload["lat"], payload["lng"]),
        "phone": payload.get("location_phone") or payload.get("phone", ""),
        "hours_of_operation": payload.get("hours_of_operation", {}),
        "is_active": True,
    }
    first_location = business.locations.order_by("created_at").first()
    if first_location is None:
        BusinessLocation.objects.create(business=business, **location_defaults)
    else:
        for field, value in location_defaults.items():
            setattr(first_location, field, value)
        first_location.save()

    _notify_sales_team(business)
    return business


def bag_has_sales(bag: Bag) -> bool:
    return (
        Order.objects.filter(bag=bag)
        .exclude(
            status__in=(
                OrderStatus.CANCELLED,
                OrderStatus.EXPIRED,
            )
        )
        .exists()
    )


def assert_bag_editable(bag: Bag) -> None:
    if bag_has_sales(bag):
        raise BagEditNotAllowed("Bags with sales can no longer be edited.")


@transaction.atomic
def duplicate_bag(*, bag: Bag, overrides: dict | None = None) -> Bag:
    overrides = overrides or {}
    duration = bag.pickup_window_end - bag.pickup_window_start
    if duration <= timedelta(0):
        duration = timedelta(hours=2)
    start = overrides.get("pickup_window_start") or (timezone.now() + timedelta(hours=2))
    end = overrides.get("pickup_window_end") or (start + duration)
    quantity_available = overrides.get("quantity_available") or bag.quantity_total or 1

    clone = Bag.objects.create(
        business_location_id=overrides.get("business_location_id") or bag.business_location_id,
        type=bag.type,
        title=bag.title,
        description=bag.description,
        image_url=bag.image_url,
        extra_image_urls=bag.extra_image_urls,
        original_price=bag.original_price,
        sale_price=bag.sale_price,
        quantity_available=quantity_available,
        pickup_window_start=start,
        pickup_window_end=end,
        is_active=True,
        is_suspended_meal_eligible=bag.is_suspended_meal_eligible,
    )
    clone.dietary_tags.set(bag.dietary_tags.all())
    clone.allergen_warnings.set(bag.allergen_warnings.all())
    return clone


def _store_verification_files(*, files: dict, tier: str) -> UploadedVerificationFiles:
    uploaded = UploadedVerificationFiles()
    field_map = {
        "ruc_document": ("ruc_document_url", "business/onboarding/ruc"),
        "cedula_document": ("cedula_document_url", "business/onboarding/cedula"),
        "selfie_with_cedula": (
            "selfie_with_cedula_url",
            "business/onboarding/selfie-with-cedula",
        ),
        "permiso_funcionamiento": (
            "permiso_funcionamiento_url",
            "business/onboarding/permiso",
        ),
        "arcsa_document": ("arcsa_url", "business/onboarding/arcsa"),
        "bank_proof": ("bank_proof_url", "business/onboarding/bank-proof"),
        "business_photo": ("business_photo_url", "business/onboarding/business-photo"),
    }
    for field_name, (attr, prefix) in field_map.items():
        file = files.get(field_name)
        if file is not None:
            setattr(uploaded, attr, store_uploaded_file(file, prefix=prefix))
        elif tier == BusinessTier.INFORMAL and field_name in {
            "ruc_document",
            "permiso_funcionamiento",
            "arcsa_document",
            "bank_proof",
        }:
            continue
    return uploaded


def _build_bank_account(payload: dict) -> dict:
    if payload["payout_method"] == "de_una":
        return {
            "method": "de_una",
            "holder": payload["account_holder"],
            "phone": payload["deuna_phone"],
        }
    return {
        "method": "bank_transfer",
        "holder": payload["account_holder"],
        "bank_name": payload["bank_name"],
        "account_number": payload["account_number"],
        "account_type": payload.get("account_type", "checking"),
    }


def _notify_sales_team(business: Business) -> None:
    recipients = list(
        User.objects.filter(role=User.Role.SALES_REP, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    if not recipients:
        return
    send_mail(
        subject=f"Nueva solicitud de negocio: {business.name}",
        message=(
            f"{business.name} acaba de enviar su onboarding.\n"
            f"Tipo: {business.business_type}\n"
            f"Tier: {business.tier}\n"
            f"Propietario: {business.owner.email}"
        ),
        from_email=None,
        recipient_list=recipients,
        fail_silently=True,
    )
