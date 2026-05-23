from django.contrib import admin

from .models import AdCampaign


@admin.register(AdCampaign)
class AdCampaignAdmin(admin.ModelAdmin):
    list_display = ("business", "type", "status", "start_date", "end_date", "budget")
    list_filter = ("type", "status")
    raw_id_fields = ("business",)
