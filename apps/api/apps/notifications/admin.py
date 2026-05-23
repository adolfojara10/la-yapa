from django.contrib import admin

from .models import NotificationPreference, PushToken


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "last_minute_deals", "pickup_reminders", "marketing")
    raw_id_fields = ("user",)


@admin.register(PushToken)
class PushTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "is_active", "created_at")
    list_filter = ("platform", "is_active")
    search_fields = ("user__email", "token")
    raw_id_fields = ("user",)
