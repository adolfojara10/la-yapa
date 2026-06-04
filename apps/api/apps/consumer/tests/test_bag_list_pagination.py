"""Cursor pagination behavior."""

from __future__ import annotations

import pytest
from django.urls import reverse

URL = reverse("v1:consumer:bag-list")


@pytest.mark.django_db
def test_default_page_size_is_20(authed, make_bag):
    for _ in range(25):
        make_bag()
    response = authed.get(URL)
    body = response.json()
    assert len(body["results"]) == 20
    assert body["next"] is not None


@pytest.mark.django_db
def test_cursor_round_trip_returns_remaining_items(authed, make_bag):
    bags = [make_bag() for _ in range(25)]
    first = authed.get(URL).json()
    second = authed.get(first["next"]).json()
    first_ids = {b["id"] for b in first["results"]}
    second_ids = {b["id"] for b in second["results"]}
    assert first_ids.isdisjoint(second_ids)
    assert len(first_ids) + len(second_ids) == len(bags)


@pytest.mark.django_db
def test_page_size_query_param_respected_up_to_max(authed, make_bag):
    for _ in range(15):
        make_bag()
    response = authed.get(URL, {"page_size": 5})
    assert len(response.json()["results"]) == 5
    # Over the max — clamps to 50; we only created 15, so we get 15.
    response = authed.get(URL, {"page_size": 999})
    assert len(response.json()["results"]) == 15
