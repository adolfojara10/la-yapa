"""Reusable model mixins. Every domain model inherits TimestampedModel."""

import uuid

from django.db import models


class TimestampedModel(models.Model):
    """Adds created_at + updated_at to every model.

    Inherit from this for new tables — the schema spec mandates updated_at
    everywhere, and centralizing it avoids drift.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDPrimaryKeyModel(models.Model):
    """Mixin that swaps the default integer PK for a UUID.

    Used by models whose IDs leak into URLs/QR codes/tokens where a sequential
    integer is a security smell (Order, Bag, SuspendedMealDonation, Dispute).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
