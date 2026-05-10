from django.contrib import admin

from dashboard.models import DailyUsageStat, ModelPricing


@admin.register(DailyUsageStat)
class DailyUsageStatAdmin(admin.ModelAdmin):
    list_display = ("stat_date", "model_name", "total_requests", "total_tokens", "total_cost", "error_count")
    search_fields = ("model_name",)


@admin.register(ModelPricing)
class ModelPricingAdmin(admin.ModelAdmin):
    list_display = ("model_name", "prompt_price_per_million", "completion_price_per_million", "cached_price_per_million", "updated_at")
    search_fields = ("model_name",)
    list_filter = ("model_name",)
