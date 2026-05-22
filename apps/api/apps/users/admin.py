from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "role", "is_staff", "created_at")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "username", "phone")
    ordering = ("-created_at",)

    fieldsets = (
        *UserAdmin.fieldsets,
        ("La Yapa", {"fields": ("role", "phone", "locale")}),
    )
