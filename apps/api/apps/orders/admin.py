from django.contrib import admin

from .models import Dispute, Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "short_id",
        "consumer",
        "business_location",
        "status",
        "total_paid",
        "pickup_code",
        "created_at",
    )
    list_filter = ("status", "payment_method", "cancelled_by")
    search_fields = ("id", "pickup_code", "consumer__email", "payment_provider_ref")
    raw_id_fields = ("consumer", "bag", "business_location")
    readonly_fields = ("pickup_code", "pickup_qr_token")
    date_hierarchy = "created_at"

    @admin.display(description="ID")
    def short_id(self, obj):
        return str(obj.id)[:8]


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "opened_by", "status", "resolved_by", "created_at")
    list_filter = ("status", "opened_by")
    search_fields = ("order__id", "reason")
    raw_id_fields = ("order", "resolved_by")
