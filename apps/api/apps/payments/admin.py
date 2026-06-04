from django.contrib import admin

from .models import (
    BonusCredit,
    Invoice,
    PaymentTransaction,
    Payout,
    PayoutLineItem,
    WebhookEventLog,
)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("provider_transaction_id", "provider", "amount", "status", "created_at")
    list_filter = ("provider", "status", "currency")
    search_fields = ("provider_transaction_id", "order__id")
    raw_id_fields = ("order",)


class PayoutLineItemInline(admin.TabularInline):
    model = PayoutLineItem
    extra = 0
    raw_id_fields = ("order",)


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("business", "period_start", "period_end", "total_amount", "status")
    list_filter = ("status",)
    search_fields = ("business__name", "bank_reference")
    raw_id_fields = ("business", "approved_by")
    inlines = [PayoutLineItemInline]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("sri_authorization_number", "type", "status", "order", "created_at")
    list_filter = ("type", "status")
    search_fields = ("sri_authorization_number", "order__id")
    raw_id_fields = ("order",)


@admin.register(BonusCredit)
class BonusCreditAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "source", "expires_at", "redeemed_at", "created_at")
    list_filter = ("source",)
    search_fields = ("user__email", "notes")
    raw_id_fields = ("user", "source_business", "source_order", "redeemed_in_order")


@admin.register(WebhookEventLog)
class WebhookEventLogAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_type", "provider_event_id", "received_ip", "created_at")
    list_filter = ("provider", "event_type")
    search_fields = ("provider_event_id",)
    readonly_fields = (
        "provider",
        "provider_event_id",
        "event_type",
        "received_ip",
        "payload",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False
