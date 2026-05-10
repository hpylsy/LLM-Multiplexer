from django.db import models


class DailyUsageStat(models.Model):
    stat_date = models.DateField(db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    total_requests = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveBigIntegerField(default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    error_count = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    active_keys = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-stat_date", "model_name"]
        unique_together = [("stat_date", "model_name")]

    def __str__(self):
        return f"{self.stat_date} - {self.model_name}"


class ModelPricing(models.Model):
    model_name = models.CharField(max_length=100, unique=True)
    prompt_price_per_million = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    completion_price_per_million = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    cached_price_per_million = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["model_name"]

    def __str__(self):
        return self.model_name
