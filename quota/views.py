from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from api_keys.models import APIKey
from quota.models import UserQuotaSnapshot
from usage.models import UsageLog


@login_required
def my_quota(request):
    today = date.today()

    # Time range selection
    range_name = request.GET.get("range", "this_month")
    now = timezone.localtime()
    if range_name == "today":
        range_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        range_label = "今日"
    elif range_name == "last_7_days":
        range_start = now - timedelta(days=7)
        range_label = "近 7 天"
    elif range_name == "last_30_days":
        range_start = now - timedelta(days=30)
        range_label = "近 30 天"
    elif range_name == "all":
        range_start = None
        range_label = "全部"
    else:
        range_name = "this_month"
        range_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        range_label = "本月"

    # Real-time usage aggregation from UsageLog
    user_logs = UsageLog.objects.filter(user=request.user)
    if range_start:
        user_logs = user_logs.filter(request_time__gte=range_start)

    usage_stats = user_logs.aggregate(
        total_tokens=Sum("total_tokens"),
        total_cost=Sum("estimated_cost"),
        total_requests=Count("id"),
        error_count=Count("id", filter=Q(is_error=True)),
    )

    model_breakdown = list(
        user_logs.values("model_name")
        .annotate(total_tokens=Sum("total_tokens"), total_requests=Count("id"))
        .order_by("-total_tokens")[:10]
    )

    # Quota snapshot (still show current month limits)
    snapshot = UserQuotaSnapshot.objects.filter(user=request.user, year=today.year, month=today.month).first()
    snapshots = UserQuotaSnapshot.objects.filter(user=request.user)[:12]
    bound_keys = APIKey.objects.filter(user=request.user, status=APIKey.STATUS_ACTIVE).order_by("-created_at")

    return render(request, "quota/my_quota.html", {
        "snapshot": snapshot,
        "snapshots": snapshots,
        "bound_keys": bound_keys,
        "cliproxy_base_url": f"{settings.CLIPROXY_BASE_URL.rstrip('/')}/v1",
        "range_name": range_name,
        "range_label": range_label,
        "usage_stats": usage_stats,
        "model_breakdown": model_breakdown,
    })
