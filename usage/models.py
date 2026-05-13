from django.conf import settings
from django.db import models


class UsageLog(models.Model):
    request_id = models.CharField(max_length=128, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="usage_logs")
    api_key = models.ForeignKey("api_keys.APIKey", on_delete=models.SET_NULL, null=True, blank=True, related_name="usage_logs")
    user_identifier = models.CharField(max_length=150, blank=True)
    api_key_identifier = models.CharField(max_length=150, blank=True)
    model_name = models.CharField(max_length=100, db_index=True)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    status_code = models.PositiveIntegerField(default=200)
    is_error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    request_time = models.DateTimeField(db_index=True)
    raw_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Extended fields for request events (from usage-queue)
    latency_ms = models.PositiveIntegerField(default=0)
    cached_tokens = models.PositiveIntegerField(default=0)
    reasoning_tokens = models.PositiveIntegerField(default=0)
    provider = models.CharField(max_length=50, blank=True, db_index=True)

    class Meta:
        ordering = ["-request_time"]
        indexes = [
            models.Index(fields=["request_time", "model_name"]),
            models.Index(fields=["user", "request_time"]),
            models.Index(fields=["api_key", "request_time"]),
        ]

    def __str__(self):
        return f"{self.request_id} - {self.model_name}"


class UsageImportJob(models.Model):
    SOURCE_UPLOAD = "upload"
    SOURCE_COMMAND = "command"
    SOURCE_API = "api"
    SOURCE_CHOICES = [
        (SOURCE_UPLOAD, "页面上传"),
        (SOURCE_COMMAND, "管理命令"),
        (SOURCE_API, "接口同步"),
    ]

    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    source_name = models.CharField(max_length=255)
    imported_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    summary = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source_type}:{self.source_name}"
