from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    ConsumerProfile,
    DietaryTag,
    EmailVerificationCode,
    PasswordResetToken,
    User,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "role", "is_premium", "is_staff", "created_at")
    list_filter = ("role", "is_premium", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "username", "phone")
    ordering = ("-created_at",)

    fieldsets = (
        *UserAdmin.fieldsets,
        (
            "La Yapa",
            {
                "fields": (
                    "role",
                    "phone",
                    "language",
                    "is_email_verified",
                    "email_verified_at",
                    "is_premium",
                    "premium_expires_at",
                )
            },
        ),
    )
    readonly_fields = ("email_verified_at",)


@admin.register(ConsumerProfile)
class ConsumerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "referral_code", "created_at")
    search_fields = ("user__email", "first_name", "last_name", "referral_code")
    raw_id_fields = ("user", "referred_by")


@admin.register(DietaryTag)
class DietaryTagAdmin(admin.ModelAdmin):
    list_display = ("name", "label_es", "label_en")
    search_fields = ("name", "label_es")


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "attempts", "expires_at", "consumed_at", "created_at")
    list_filter = ("consumed_at",)
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
    readonly_fields = (
        "user",
        "code",
        "expires_at",
        "consumed_at",
        "attempts",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    # Deliberately omit `token_hash` from list_display — it's sensitive even hashed.
    list_display = ("user", "expires_at", "consumed_at", "created_at")
    list_filter = ("consumed_at",)
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
    readonly_fields = ("user", "expires_at", "consumed_at", "created_at", "updated_at")
    exclude = ("token_hash",)

    def has_add_permission(self, request):
        return False
