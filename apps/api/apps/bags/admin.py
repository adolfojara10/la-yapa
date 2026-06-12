from django.contrib import admin

from .models import AllergenTag, Bag, BagTemplate


@admin.register(Bag)
class BagAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "business_location",
        "type",
        "sale_price",
        "original_price",
        "discount_percent",
        "quantity_available",
        "pickup_window_start",
        "is_active",
    )
    list_filter = ("type", "is_active", "is_suspended_meal_eligible")
    search_fields = ("title", "business_location__name", "business_location__business__name")
    raw_id_fields = ("business_location",)
    filter_horizontal = ("dietary_tags", "allergen_warnings")
    readonly_fields = ("quantity_total",)


@admin.register(AllergenTag)
class AllergenTagAdmin(admin.ModelAdmin):
    list_display = ("name", "label_es", "label_en")
    search_fields = ("name", "label_es")


@admin.register(BagTemplate)
class BagTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "type", "sale_price", "original_price")
    search_fields = ("name", "title", "business__name")
    raw_id_fields = ("business",)
    filter_horizontal = ("dietary_tags", "allergen_warnings")
