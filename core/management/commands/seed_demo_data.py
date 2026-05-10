from datetime import timedelta
from decimal import Decimal
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from api_keys.models import APIKey, APIKeyRequest
from dashboard.services import rebuild_daily_usage_stats
from quota.models import UserQuotaSnapshot
from usage.models import UsageLog
from users.models import Profile


class Command(BaseCommand):
    help = "生成演示用户、Key、Usage 和额度快照"

    def handle(self, *args, **options):
        User = get_user_model()
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
        )
        admin.set_password("Admin123456!")
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        users = []
        for idx in range(1, 6):
            user, _ = User.objects.get_or_create(
                username=f"user{idx:02d}",
                defaults={"email": f"user{idx:02d}@example.com", "first_name": f"用户{idx}"},
            )
            user.set_password("User123456!")
            user.save()
            profile = user.profile
            profile.display_name = f"实验室成员{idx}"
            profile.lab_group = f"Group-{(idx % 2) + 1}"
            profile.monthly_token_quota = 2_000_000
            profile.monthly_cost_quota = Decimal("100.0000")
            profile.is_dashboard_visible = True
            profile.role = Profile.ROLE_USER
            profile.save()
            users.append(user)

        model_names = ["gpt-4o-mini", "gpt-4.1", "claude-3-5-sonnet", "gemini-2.5-pro"]
        now = timezone.now()

        for idx, user in enumerate(users, start=1):
            raw_token = APIKey.generate_token()
            metadata = APIKey.build_token_metadata(raw_token)
            APIKey.objects.get_or_create(
                user=user,
                name=f"default-{idx}",
                defaults={
                    "token_hash": metadata["token_hash"],
                    "token_prefix": metadata["token_prefix"],
                    "token_masked": metadata["token_masked"],
                    "status": APIKey.STATUS_ACTIVE,
                },
            )
            APIKeyRequest.objects.get_or_create(
                user=user,
                name=f"research-{idx}",
                defaults={
                    "reason": "用于实验室模型测试",
                    "requested_models": ", ".join(model_names[:2]),
                    "requested_quota": 500000,
                    "status": APIKeyRequest.STATUS_PENDING,
                },
            )

        for user in users:
            key = user.api_keys.first()
            for day_offset in range(0, 30):
                request_count = random.randint(2, 6)
                for req_idx in range(request_count):
                    prompt_tokens = random.randint(100, 1200)
                    completion_tokens = random.randint(50, 1000)
                    total_tokens = prompt_tokens + completion_tokens
                    is_error = random.random() < 0.08
                    request_time = now - timedelta(days=day_offset, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                    UsageLog.objects.get_or_create(
                        request_id=f"demo-{user.username}-{day_offset}-{req_idx}",
                        defaults={
                            "user": user,
                            "api_key": key,
                            "user_identifier": user.username,
                            "api_key_identifier": key.token_prefix if key else "",
                            "model_name": random.choice(model_names),
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": total_tokens,
                            "estimated_cost": Decimal(total_tokens) / Decimal("500000"),
                            "status_code": 500 if is_error else 200,
                            "is_error": is_error,
                            "error_message": "upstream timeout" if is_error else "",
                            "request_time": request_time,
                            "raw_payload": {"demo": True},
                        },
                    )

            for month_back in range(0, 4):
                target = (now - timedelta(days=30 * month_back))
                UserQuotaSnapshot.objects.get_or_create(
                    user=user,
                    year=target.year,
                    month=target.month,
                    defaults={
                        "token_limit": 2_000_000,
                        "token_used": random.randint(300000, 1600000),
                        "cost_limit": Decimal("100.0000"),
                        "cost_used": Decimal(str(round(random.uniform(10, 80), 4))),
                    },
                )

        count = rebuild_daily_usage_stats(days=90)
        self.stdout.write(self.style.SUCCESS(f"演示数据已生成，DailyUsageStat={count}"))
        self.stdout.write("管理员账号: admin / Admin123456!")
        self.stdout.write("测试用户账号: user01-user05 / User123456!")
