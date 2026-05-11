from django.contrib import admin
from django.contrib.auth.models import Group

from users.models import PremiumApplication

admin.site.unregister(Group)


@admin.register(PremiumApplication)
class PremiumApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "is_premium", "created_at", "updated_at",)
    list_per_page = 50
    readonly_fields = ("user", "created_at", "updated_at",)
    fields = ("user", "is_premium", "created_at", "updated_at",)
    ordering = ("-created_at", "-updated_at",)
