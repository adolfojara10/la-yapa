from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ConsumerProfile, DietaryTag, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "role", "is_premium", "is_staff", "created_at")
    list_filter = ("role", "is_premium", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "username", "phone")
    ordering = ("-created_at",)

    fieldsets = (
        *UserAdmin.fieldsets,
        ("La Yapa", {"fields": ("role", "phone", "language", "is_premium", "premium_expires_at")}),
    )


@admin.register(ConsumerProfile)
class ConsumerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "referral_code", "created_at")
    search_fields = ("user__email", "first_name", "last_name", "referral_code")
    raw_id_fields = ("user", "referred_by")


@admin.register(DietaryTag)
class DietaryTagAdmin(admin.ModelAdmin):
    list_display = ("name", "label_es", "label_en")
    search_fields = ("name", "label_es")
