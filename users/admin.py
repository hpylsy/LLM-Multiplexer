from django.contrib import admin

from users.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "role", "lab_group", "is_dashboard_visible", "monthly_token_quota")
    search_fields = ("user__username", "display_name", "email", "lab_group")
    list_filter = ("role", "is_dashboard_visible", "lab_group")
