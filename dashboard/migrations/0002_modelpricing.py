from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModelPricing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("model_name", models.CharField(max_length=100, unique=True)),
                ("prompt_price_per_million", models.DecimalField(decimal_places=6, default=0, max_digits=12)),
                ("completion_price_per_million", models.DecimalField(decimal_places=6, default=0, max_digits=12)),
                ("cached_price_per_million", models.DecimalField(decimal_places=6, default=0, max_digits=12)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["model_name"]},
        ),
    ]
