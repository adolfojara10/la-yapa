from django.contrib import admin

from .models import ImpactStat


@admin.register(ImpactStat)
class ImpactStatAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "meals_rescued",
        "kg_food_saved",
        "co2_kg_saved",
        "money_saved",
        "last_calculated_at",
    )
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
