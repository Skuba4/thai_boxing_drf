from django.contrib import admin

from users.models import PremiumApplication


@admin.register(PremiumApplication)
class PremiumApplicationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "status")
    list_per_page = 20
    readonly_fields = ("created_at", "user")
    fields = ("created_at", "user", "status")
    ordering = ("created_at", "user", "status")
