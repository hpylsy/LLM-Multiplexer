from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from core.utils import admin_required
from dashboard.forms import ModelPricingForm
from dashboard.models import ModelPricing
from usage.models import UsageLog
from usage.services import aggregate_dashboard


def _get_range_start(range_name):
    now = timezone.localtime()
    if range_name == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if range_name == "this_month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return now - timedelta(days=7)


def _build_personal_dashboard_summary(user, visible_logs, personal_logs):
    user_rank_rows = list(
        visible_logs.exclude(user=None)
        .values("user_id", "user__username", "user__profile__display_name")
        .annotate(total_tokens=Sum("total_tokens"))
        .order_by("-total_tokens")
    )
    user_rank = len(user_rank_rows)
    total_users = len(user_rank_rows)
    for index, row in enumerate(user_rank_rows, start=1):
        if row["user_id"] == user.id:
            user_rank = index
            break

    model_usage = list(
        personal_logs.values("model_name")
        .annotate(total_tokens=Sum("total_tokens"))
        .order_by("-total_tokens")
    )

    return {
        "total_tokens": sum(item["total_tokens"] or 0 for item in model_usage),
        "models": model_usage,
        "rank": user_rank,
        "total_users": total_users,
        "model_count": len(model_usage),
        "top_model": model_usage[0]["model_name"] if model_usage else "暂无",
    }


def _display_name_strict(display_name, username):
    value = (display_name or "").strip()
    if value:
        return value
    return "未设置显示名"


def _get_filter_options():
    """Get group and grade filter options (cached query)."""
    groups = sorted({
        group for group in
        UsageLog.objects.exclude(user=None)
        .exclude(user__profile__lab_group="")
        .values_list("user__profile__lab_group", flat=True).distinct()
        if group in {"电控", "算法", "机械", "宣传"}
    })
    grades = sorted({
        grade for grade in
        UsageLog.objects.exclude(user=None)
        .exclude(user__profile__grade="")
        .values_list("user__profile__grade", flat=True).distinct()
        if grade
    })
    return groups, grades


def _enrich_display_names(data):
    """Add display_name to user_rank, recent_errors, recent_active_users."""
    for row in data["user_rank"]:
        row["display_name"] = _display_name_strict(row.get("user__profile__display_name"), row.get("user__username"))
    for item in data["recent_errors"]:
        if item.user_id and hasattr(item.user, "profile"):
            item.display_name = _display_name_strict(item.user.profile.display_name, item.user.username)
        else:
            item.display_name = "-"
    for row in data["recent_active_users"]:
        row["display_name"] = _display_name_strict(row.get("user__profile__display_name"), row.get("user__username"))


@login_required
def public_dashboard(request):
    if not settings.PUBLIC_DASHBOARD_ENABLED and not request.user.is_staff:
        return render(request, "dashboard/dashboard_unavailable.html")

    range_name = request.GET.get("range", "today")
    group_name = request.GET.get("group", "all")
    grade_name = request.GET.get("grade", "all")

    all_logs = UsageLog.objects.filter(request_time__gte=_get_range_start(range_name)).exclude(user=None)
    visible_logs = all_logs
    if not request.user.is_staff:
        visible_logs = visible_logs.filter(user__profile__is_dashboard_visible=True)
    if group_name != "all":
        visible_logs = visible_logs.filter(user__profile__lab_group=group_name)
    if grade_name != "all":
        visible_logs = visible_logs.filter(user__profile__grade=grade_name)

    data = aggregate_dashboard(visible_logs, trend_bucket="hour" if range_name == "today" else "day")
    _enrich_display_names(data)

    personal_summary = None
    if not request.user.is_staff:
        personal_logs = all_logs.filter(user=request.user)
        personal_summary = _build_personal_dashboard_summary(request.user, visible_logs, personal_logs)

    groups, grades = _get_filter_options()
    return render(request, "dashboard/public_dashboard.html", {
        "dashboard": data,
        "range_name": range_name,
        "personal_summary": personal_summary,
        "group_name": group_name,
        "group_options": groups,
        "grade_name": grade_name,
        "grade_options": grades,
        "enable_auto_sync": True,
    })


@admin_required
def admin_dashboard(request):
    range_name = request.GET.get("range", "today")
    group_name = request.GET.get("group", "all")
    grade_name = request.GET.get("grade", "all")

    logs = UsageLog.objects.filter(request_time__gte=_get_range_start(range_name)).exclude(user=None)
    if group_name != "all":
        logs = logs.filter(user__profile__lab_group=group_name)
    if grade_name != "all":
        logs = logs.filter(user__profile__grade=grade_name)

    data = aggregate_dashboard(logs, trend_bucket="hour" if range_name == "today" else "day")
    _enrich_display_names(data)

    groups, grades = _get_filter_options()
    return render(request, "dashboard/admin_dashboard.html", {
        "dashboard": data,
        "range_name": range_name,
        "group_name": group_name,
        "group_options": groups,
        "grade_name": grade_name,
        "grade_options": grades,
        "enable_auto_sync": True,
    })


@admin_required
def model_pricing_admin(request):
    if request.method == "POST":
        form = ModelPricingForm(request.POST)
        if form.is_valid():
            ModelPricing.objects.update_or_create(
                model_name=form.cleaned_data["model_name"],
                defaults={
                    "prompt_price_per_million": form.cleaned_data["prompt_price_per_million"],
                    "completion_price_per_million": form.cleaned_data["completion_price_per_million"],
                    "cached_price_per_million": form.cleaned_data["cached_price_per_million"],
                },
            )
            form = ModelPricingForm()
    else:
        form = ModelPricingForm()
    pricings = ModelPricing.objects.all()
    return render(request, "dashboard/model_pricing_admin.html", {"form": form, "pricings": pricings})
