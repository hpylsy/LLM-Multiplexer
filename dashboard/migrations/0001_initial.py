from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DailyUsageStat",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("stat_date", models.DateField(db_index=True)),
                ("model_name", models.CharField(db_index=True, max_length=100)),
                ("total_requests", models.PositiveIntegerField(default=0)),
                ("total_tokens", models.PositiveBigIntegerField(default=0)),
                ("total_cost", models.DecimalField(decimal_places=6, default=0, max_digits=12)),
                ("error_count", models.PositiveIntegerField(default=0)),
                ("active_users", models.PositiveIntegerField(default=0)),
                ("active_keys", models.PositiveIntegerField(default=0)),
            ],
            options={"ordering": ["-stat_date", "model_name"], "unique_together": {("stat_date", "model_name")}},
        ),
    ]
