from datetime import timedelta

from django.utils import timezone

from dashboard.models import DailyUsageStat
from usage.models import UsageLog


def rebuild_daily_usage_stats(days=90):
    end_time = timezone.now()
    start_time = end_time - timedelta(days=days)
    DailyUsageStat.objects.filter(stat_date__gte=start_time.date()).delete()

    logs = UsageLog.objects.filter(request_time__gte=start_time).order_by("request_time")
    bucket = {}
    for item in logs:
        stat_date = timezone.localtime(item.request_time).date()
        key = (stat_date, item.model_name)
        if key not in bucket:
            bucket[key] = {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "error_count": 0,
                "users": set(),
                "keys": set(),
            }
        row = bucket[key]
        row["total_requests"] += 1
        row["total_tokens"] += item.total_tokens
        row["total_cost"] += float(item.estimated_cost)
        row["error_count"] += 1 if item.is_error else 0
        if item.user_id:
            row["users"].add(item.user_id)
        if item.api_key_id:
            row["keys"].add(item.api_key_id)

    objects = []
    for (stat_date, model_name), row in bucket.items():
        objects.append(DailyUsageStat(
            stat_date=stat_date,
            model_name=model_name,
            total_requests=row["total_requests"],
            total_tokens=row["total_tokens"],
            total_cost=row["total_cost"],
            error_count=row["error_count"],
            active_users=len(row["users"]),
            active_keys=len(row["keys"]),
        ))
    DailyUsageStat.objects.bulk_create(objects)
    return len(objects)
