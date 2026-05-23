from django.contrib import admin

from .models import SuspendedMealClaim, SuspendedMealDonation


@admin.register(SuspendedMealDonation)
class SuspendedMealDonationAdmin(admin.ModelAdmin):
    list_display = ("id", "donor", "amount", "status", "is_anonymous", "created_at")
    list_filter = ("status", "is_anonymous")
    search_fields = ("donor__email",)
    raw_id_fields = ("donor", "bag", "claimed_by_business")


@admin.register(SuspendedMealClaim)
class SuspendedMealClaimAdmin(admin.ModelAdmin):
    list_display = ("donation", "business_location", "claimed_at")
    raw_id_fields = ("donation", "business_location")
