"""Cursor pagination for the bag list.

DRF's stock `CursorPagination` insists on a single ordering field. Our
preferred sort is `(distance_m, id)` (when geo) or `(pickup_window_end,
id)` (when not) — composite. We subclass + override `ordering` per-request
via a small dance: the view sets `paginator.ordering` before calling
`paginate_queryset`.

Stability under writes: ordering ties broken by `id` (UUID for bags) means
new/expired bags don't shift the cursor.
"""

from __future__ import annotations

from rest_framework.pagination import CursorPagination


class BagCursorPagination(CursorPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50
    cursor_query_param = "cursor"
    # Default; the view replaces this per-request based on `sort` + has_location.
    ordering = ("pickup_window_end", "id")
