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
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(blank=True, max_length=150)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("role", models.CharField(choices=[("user", "普通用户"), ("admin", "管理员")], default="user", max_length=20)),
                ("lab_group", models.CharField(blank=True, max_length=100)),
                ("is_dashboard_visible", models.BooleanField(default=True)),
                ("monthly_token_quota", models.PositiveBigIntegerField(default=0)),
                ("monthly_cost_quota", models.DecimalField(decimal_places=4, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["user__username"]},
        ),
    ]
