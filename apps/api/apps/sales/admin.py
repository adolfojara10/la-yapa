from django.contrib import admin

from .models import SalesRepProfile


@admin.register(SalesRepProfile)
class SalesRepProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "commission_rate")
    raw_id_fields = ("user",)
    filter_horizontal = ("businesses_onboarded",)
