from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserQuotaSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveIntegerField()),
                ("month", models.PositiveIntegerField()),
                ("token_limit", models.PositiveBigIntegerField(default=0)),
                ("token_used", models.PositiveBigIntegerField(default=0)),
                ("cost_limit", models.DecimalField(decimal_places=4, default=0, max_digits=12)),
                ("cost_used", models.DecimalField(decimal_places=4, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quota_snapshots", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-year", "-month", "user__username"], "unique_together": {("user", "year", "month")}},
        ),
    ]
