from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="lab_group",
            field=models.CharField(blank=True, choices=[("电控", "电控"), ("算法", "算法"), ("机械", "机械"), ("宣传", "宣传")], max_length=100),
        ),
        migrations.AddField(
            model_name="profile",
            name="member_type",
            field=models.CharField(blank=True, choices=[("正式队员", "正式队员"), ("梯队队员", "梯队队员")], default="正式队员", max_length=30),
        ),
    ]
