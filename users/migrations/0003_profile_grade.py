from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_profile_member_type_alter_profile_lab_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="grade",
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
