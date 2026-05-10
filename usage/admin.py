from django.contrib import admin

from usage.models import UsageImportJob, UsageLog


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ("request_id", "user", "api_key", "model_name", "total_tokens", "estimated_cost", "status_code", "request_time")
    search_fields = ("request_id", "user__username", "model_name", "api_key__name")
    list_filter = ("model_name", "is_error", "status_code", "request_time")
    date_hierarchy = "request_time"


@admin.register(UsageImportJob)
class UsageImportJobAdmin(admin.ModelAdmin):
    list_display = ("source_type", "source_name", "imported_count", "skipped_count", "failed_count", "created_at")
    search_fields = ("source_name",)
    list_filter = ("source_type", "created_at")
