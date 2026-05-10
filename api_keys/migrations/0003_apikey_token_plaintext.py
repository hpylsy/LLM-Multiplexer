from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api_keys", "0002_apikey_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="apikey",
            name="token_plaintext",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
