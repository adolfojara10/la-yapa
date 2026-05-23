from django.contrib import admin

from .models import Badge, Referral, UserBadge, UserLevel


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "rarity")
    list_filter = ("category", "rarity")
    search_fields = ("name", "description")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "earned_at")
    raw_id_fields = ("user", "badge")


@admin.register(UserLevel)
class UserLevelAdmin(admin.ModelAdmin):
    list_display = ("user", "level_name", "xp_total", "meals_rescued", "current_streak_weeks")
    list_filter = ("level_name",)
    search_fields = ("user__email",)
    raw_id_fields = ("user",)


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("referrer", "referred", "status", "reward_credit_amount", "completed_at")
    list_filter = ("status",)
    raw_id_fields = ("referrer", "referred")
