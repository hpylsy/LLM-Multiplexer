from django.contrib import admin

from quota.models import UserQuotaSnapshot


@admin.register(UserQuotaSnapshot)
class UserQuotaSnapshotAdmin(admin.ModelAdmin):
    list_display = ("user", "year", "month", "token_limit", "token_used", "cost_limit", "cost_used")
    search_fields = ("user__username",)
    list_filter = ("year", "month")
