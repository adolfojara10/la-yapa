from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("rating", "consumer", "business_location", "is_visible", "created_at")
    list_filter = ("rating", "is_visible")
    search_fields = ("consumer__email", "business_location__name", "comment")
    raw_id_fields = ("order", "consumer", "business_location")
