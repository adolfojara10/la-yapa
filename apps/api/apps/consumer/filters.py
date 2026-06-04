"""Query-param filters for /consumer/bags.

We don't use django-filter's `FilterSet` here because most of our filters
need cross-table semantics (M2M AND on dietary, M2M exclusion on allergens,
annotated rating subqueries) that don't fit FilterSet's declarative model
cleanly. A plain function `apply_filters(qs, params)` is easier to read
and easier to test in isolation.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Avg, Count, Q, QuerySet
from django.utils import timezone

# ---- public surface --------------------------------------------------------

PICKUP_TODAY = "today"
PICKUP_TOMORROW = "tomorrow"
PICKUP_THIS_WEEK = "this_week"
PICKUP_CHOICES = {PICKUP_TODAY, PICKUP_TOMORROW, PICKUP_THIS_WEEK}

SORT_DISTANCE = "distance"
SORT_PRICE = "price"
SORT_RATING = "rating"
SORT_ENDING_SOON = "ending_soon"
SORT_CHOICES = {SORT_DISTANCE, SORT_PRICE, SORT_RATING, SORT_ENDING_SOON}


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def apply_filters(qs: QuerySet, params: dict[str, Any]) -> QuerySet:
    """Apply all consumer-facing filter params to `qs`.

    `qs` is expected to already be `.active()` and (optionally) annotated
    with `distance_m`. This function only adds WHERE clauses + annotations
    for rating; ordering is handled separately by `apply_sort`.
    """
    # Annotate location-level review aggregates once. Cheap because the
    # subquery is keyed off business_location_id which is indexed.
    qs = qs.annotate(
        location_rating_avg=Avg(
            "business_location__reviews__rating",
            filter=Q(business_location__reviews__is_visible=True),
        ),
        location_rating_count=Count(
            "business_location__reviews",
            filter=Q(business_location__reviews__is_visible=True),
        ),
    )

    # Dietary: AND semantics. A bag with [vegan, gluten_free] passes
    # `?dietary=vegan,gluten_free`; a bag with only [vegan] does not.
    dietary = _csv(params.get("dietary"))
    for tag in dietary:
        qs = qs.filter(dietary_tags__name=tag)

    # Allergens: exclusion / union. `?exclude_allergens=mani,gluten` removes
    # any bag whose allergen_warnings overlaps {mani, gluten}.
    excluded = _csv(params.get("exclude_allergens"))
    if excluded:
        qs = qs.exclude(allergen_warnings__name__in=excluded)

    # Price range on sale_price.
    min_price = _to_decimal(params.get("min_price"))
    if min_price is not None:
        qs = qs.filter(sale_price__gte=min_price)
    max_price = _to_decimal(params.get("max_price"))
    if max_price is not None:
        qs = qs.filter(sale_price__lte=max_price)

    # Pickup window bucket.
    window = params.get("pickup_window")
    if window in PICKUP_CHOICES:
        start, end = _pickup_bounds(window)
        qs = qs.filter(pickup_window_start__gte=start, pickup_window_start__lt=end)

    # Min rating.
    min_rating = _to_float(params.get("min_rating"))
    if min_rating is not None:
        qs = qs.filter(location_rating_avg__gte=min_rating)

    # Text search.
    q = (params.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(business_location__business__name__icontains=q))

    # M2M filters can multiply rows; collapse defensively.
    if dietary or q:
        qs = qs.distinct()

    return qs


def apply_sort(qs: QuerySet, sort: str | None, *, has_location: bool) -> QuerySet:
    """Apply ordering. Falls back to ending_soon when distance sort is
    requested but the caller didn't provide a location."""
    chosen = sort if sort in SORT_CHOICES else SORT_DISTANCE
    if chosen == SORT_DISTANCE and not has_location:
        chosen = SORT_ENDING_SOON

    if chosen == SORT_DISTANCE:
        return qs.order_by("distance_m", "id")
    if chosen == SORT_PRICE:
        return qs.order_by("sale_price", "pickup_window_end", "id")
    if chosen == SORT_RATING:
        # Nulls last is the friendly behavior — unrated places shouldn't
        # rank above 5-star places.
        from django.db.models import F

        return qs.order_by(F("location_rating_avg").desc(nulls_last=True), "id")
    # ending_soon
    return qs.order_by("pickup_window_end", "id")


# ---- internals -------------------------------------------------------------


def _pickup_bounds(window: str) -> tuple[datetime, datetime]:
    now = timezone.now()
    today = timezone.localdate()
    start_of_day = timezone.make_aware(datetime.combine(today, time.min))
    if window == PICKUP_TODAY:
        return now, start_of_day + timedelta(days=1)
    if window == PICKUP_TOMORROW:
        return start_of_day + timedelta(days=1), start_of_day + timedelta(days=2)
    # this_week: today through end-of-Sunday (ISO week).
    days_until_sunday = 6 - today.weekday()  # Monday=0 … Sunday=6
    return now, start_of_day + timedelta(days=days_until_sunday + 1)


def _to_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (ValueError, ArithmeticError):
        return None


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
