from django.contrib import admin

from .models import Business, BusinessLocation, BusinessVerification, Favorite


class BusinessLocationInline(admin.TabularInline):
    model = BusinessLocation
    extra = 0
    show_change_link = True
    fields = ("name", "address", "is_active")


class BusinessVerificationInline(admin.StackedInline):
    model = BusinessVerification
    extra = 0


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "business_type", "tier", "status", "owner", "created_at")
    list_filter = ("status", "business_type", "tier", "payout_frequency")
    search_fields = ("name", "owner__email", "phone", "email")
    raw_id_fields = ("owner", "approved_by")
    readonly_fields = ("approved_at",)
    inlines = [BusinessLocationInline, BusinessVerificationInline]
    actions = ["approve_businesses", "suspend_businesses"]

    @admin.action(description="Approve selected businesses")
    def approve_businesses(self, request, queryset):
        from django.utils import timezone

        queryset.update(status="approved", approved_at=timezone.now(), approved_by=request.user)

    @admin.action(description="Suspend selected businesses")
    def suspend_businesses(self, request, queryset):
        queryset.update(status="suspended")


@admin.register(BusinessLocation)
class BusinessLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "address", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "address", "business__name")
    raw_id_fields = ("business",)


@admin.register(BusinessVerification)
class BusinessVerificationAdmin(admin.ModelAdmin):
    list_display = ("business", "ruc_number", "cedula_number", "food_safety_terms_accepted_at")
    search_fields = ("business__name", "ruc_number", "cedula_number")
    raw_id_fields = ("business",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "business_location", "created_at")
    raw_id_fields = ("user", "business_location")
