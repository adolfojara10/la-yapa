"""Suspended-meal dispatch service.

Honor-system flow: vendor taps "Despachar" → donation flips to CLAIMED,
SuspendedMealClaim row created (audit trail), anonymous push to the donor.

Anti-abuse (MASTER_VISION §847): hard cap of 5 dispatches per
business_location per rolling 24h window. Sixth dispatch raises
DispatchRateLimitExceeded → 429 from the view.
"""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.businesses.models import BusinessLocation

from .models import DonationStatus, SuspendedMealClaim, SuspendedMealDonation

DAILY_DISPATCH_CAP_PER_LOCATION = 5


# ---- exceptions ------------------------------------------------------------


class DispatchError(Exception):
    code = "dispatch_error"

    def __init__(self, message: str = "", *, code: str | None = None):
        super().__init__(message or self.code)
        if code:
            self.code = code


class DonationNotAvailable(DispatchError):
    """Donation doesn't exist or has already been claimed/expired."""

    code = "donation_not_available"


class NotYourLocation(DispatchError):
    """Donation's bag belongs to a business this user doesn't own, and the
    request supplied an invalid business_location_id."""

    code = "not_your_location"


class DispatchRateLimitExceeded(DispatchError):
    code = "dispatch_rate_limit_exceeded"


# ---- public surface -------------------------------------------------------


def _owned_location_ids(business_owner) -> list[int]:
    return list(
        BusinessLocation.objects.filter(business__owner=business_owner)
        .order_by("id")
        .values_list("id", flat=True)
    )


@transaction.atomic
def dispatch_donation(
    *,
    business_owner,
    donation_id: str,
    business_location_id: int | None = None,
    notes: str = "",
) -> SuspendedMealClaim:
    """Dispatch (claim) an active donation for serving to a needy person.

    Routing rules:
      - If donation has `bag` set → must be served at that bag's location,
        and `business_location_id` (if supplied) must match.
      - If donation is general-pool (bag=None) → `business_location_id`
        is optional. If omitted, we default to the requester's first
        owned location (ordered by id).

    Always sends anonymous push to the donor (regardless of bag/general-pool).
    """
    owned_location_ids = _owned_location_ids(business_owner)
    if not owned_location_ids:
        raise NotYourLocation()

    try:
        donation = SuspendedMealDonation.objects.select_for_update().get(pk=donation_id)
    except (SuspendedMealDonation.DoesNotExist, ValueError):
        raise DonationNotAvailable() from None

    if donation.status != DonationStatus.ACTIVE:
        raise DonationNotAvailable()

    # Resolve effective target location.
    if donation.bag is not None:
        target_location_id = donation.bag.business_location_id
        if target_location_id not in owned_location_ids:
            raise NotYourLocation()
        if business_location_id is not None and business_location_id != target_location_id:
            raise NotYourLocation()
    else:
        if business_location_id is None:
            target_location_id = owned_location_ids[0]
        else:
            if business_location_id not in owned_location_ids:
                raise NotYourLocation()
            target_location_id = business_location_id

    # Rate-limit: max 5 dispatches per location per rolling 24h.
    recent_claims = SuspendedMealClaim.objects.filter(
        business_location_id=target_location_id,
        claimed_at__gte=timezone.now() - timedelta(days=1),
    ).count()
    if recent_claims >= DAILY_DISPATCH_CAP_PER_LOCATION:
        raise DispatchRateLimitExceeded(
            f"Daily cap of {DAILY_DISPATCH_CAP_PER_LOCATION} suspended-meal "
            f"dispatches reached for this location."
        )

    # Flip donation to CLAIMED + create the audit row.
    target_location = BusinessLocation.objects.get(pk=target_location_id)
    donation.status = DonationStatus.CLAIMED
    donation.claimed_by_business = target_location
    donation.claimed_at = timezone.now()
    donation.save(update_fields=["status", "claimed_by_business", "claimed_at", "updated_at"])

    claim = SuspendedMealClaim.objects.create(
        donation=donation,
        business_location=target_location,
        beneficiary_notes=notes,
    )

    # Anonymous push to donor — best-effort, never blocks the dispatch.
    transaction.on_commit(lambda: _notify_donor_safe(donation))

    return claim


def _notify_donor_safe(donation: SuspendedMealDonation) -> None:
    """Best-effort donor push. Errors logged; never raise."""
    import logging

    logger = logging.getLogger(__name__)
    try:
        from apps.notifications.services import send_push

        send_push(
            donation.donor,
            title="Tu yapa alimentó a alguien hoy 🌱",
            body="Una comida que donaste fue entregada. Gracias por compartir.",
            data={"donation_id": str(donation.id), "type": "suspended_meal_claimed"},
            category="order_updates",
        )
    except Exception:
        logger.exception("Donor notification failed for donation %s", donation.id)
