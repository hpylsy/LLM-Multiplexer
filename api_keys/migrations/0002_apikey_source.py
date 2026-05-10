from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api_keys", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="apikey",
            name="source",
            field=models.CharField(choices=[("portal", "Portal 生成"), ("cliproxy", "CLIProxy 绑定")], default="portal", max_length=20),
        ),
    ]
