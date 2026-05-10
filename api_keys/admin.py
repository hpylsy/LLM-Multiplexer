from django.contrib import admin

from api_keys.models import APIKey, APIKeyRequest


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "token_masked", "status", "created_at", "last_used_at")
    search_fields = ("name", "user__username", "token_prefix", "token_masked")
    list_filter = ("status", "created_at")


@admin.register(APIKeyRequest)
class APIKeyRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "status", "requested_quota", "created_at", "reviewed_at")
    search_fields = ("name", "user__username", "requested_models")
    list_filter = ("status", "created_at")
