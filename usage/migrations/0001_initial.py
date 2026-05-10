from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("api_keys", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UsageImportJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_type", models.CharField(choices=[("upload", "页面上传"), ("command", "管理命令"), ("api", "接口同步")], max_length=20)),
                ("source_name", models.CharField(max_length=255)),
                ("imported_count", models.PositiveIntegerField(default=0)),
                ("skipped_count", models.PositiveIntegerField(default=0)),
                ("failed_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("summary", models.TextField(blank=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="UsageLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_id", models.CharField(max_length=128, unique=True)),
                ("user_identifier", models.CharField(blank=True, max_length=150)),
                ("api_key_identifier", models.CharField(blank=True, max_length=150)),
                ("model_name", models.CharField(db_index=True, max_length=100)),
                ("prompt_tokens", models.PositiveIntegerField(default=0)),
                ("completion_tokens", models.PositiveIntegerField(default=0)),
                ("total_tokens", models.PositiveIntegerField(default=0)),
                ("estimated_cost", models.DecimalField(decimal_places=6, default=0, max_digits=12)),
                ("status_code", models.PositiveIntegerField(default=200)),
                ("is_error", models.BooleanField(default=False)),
                ("error_message", models.TextField(blank=True)),
                ("request_time", models.DateTimeField(db_index=True)),
                ("raw_payload", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("api_key", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="usage_logs", to="api_keys.apikey")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="usage_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-request_time"],
                "indexes": [models.Index(fields=["request_time", "model_name"], name="usage_usagel_request_9b0990_idx"), models.Index(fields=["user", "request_time"], name="usage_usagel_user_id_1ba868_idx"), models.Index(fields=["api_key", "request_time"], name="usage_usagel_api_key_0e2f8a_idx")],
            },
        ),
    ]
