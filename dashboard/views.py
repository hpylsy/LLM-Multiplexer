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


def _get_range_start(range_name, request=None):
    now = timezone.localtime()
    if range_name == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0), None
    if range_name == "this_month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), None
    if range_name == "last_30_days":
        return now - timedelta(days=30), None
    if range_name == "all":
        return None, None
    if range_name == "custom" and request:
        from django.utils.dateparse import parse_date
        start_str = request.GET.get("start", "")
        end_str = request.GET.get("end", "")
        start_date = parse_date(start_str)
        end_date = parse_date(end_str)
        if start_date and end_date:
            start_dt = timezone.make_aware(timezone.datetime(start_date.year, start_date.month, start_date.day))
            end_dt = timezone.make_aware(timezone.datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59))
            return start_dt, end_dt
    # default: last_7_days
    return now - timedelta(days=7), None


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
    """Get group and grade filter options from Profile (all registered, not just those with usage)."""
    from users.models import Profile
    groups = sorted({
        group for group in
        Profile.objects.exclude(lab_group="")
        .values_list("lab_group", flat=True).distinct()
        if group in {"电控", "算法", "机械", "宣传"}
    })
    grades = sorted({
        grade for grade in
        Profile.objects.exclude(grade="")
        .values_list("grade", flat=True).distinct()
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

    range_start, range_end = _get_range_start(range_name, request)
    all_logs = UsageLog.objects.exclude(user=None)
    if range_start:
        all_logs = all_logs.filter(request_time__gte=range_start)
    if range_end:
        all_logs = all_logs.filter(request_time__lte=range_end)

    visible_logs = all_logs
    if not request.user.is_staff:
        visible_logs = visible_logs.filter(user__profile__is_dashboard_visible=True)
    if group_name != "all":
        visible_logs = visible_logs.filter(user__profile__lab_group=group_name)
    if grade_name != "all":
        visible_logs = visible_logs.filter(user__profile__grade=grade_name)

    trend_bucket = "hour" if range_name == "today" else "day"
    data = aggregate_dashboard(visible_logs, trend_bucket=trend_bucket)
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
        "custom_start": request.GET.get("start", ""),
        "custom_end": request.GET.get("end", ""),
    })


@admin_required
def admin_dashboard(request):
    range_name = request.GET.get("range", "today")
    group_name = request.GET.get("group", "all")
    grade_name = request.GET.get("grade", "all")

    range_start, range_end = _get_range_start(range_name, request)
    logs = UsageLog.objects.exclude(user=None)
    if range_start:
        logs = logs.filter(request_time__gte=range_start)
    if range_end:
        logs = logs.filter(request_time__lte=range_end)
    if group_name != "all":
        logs = logs.filter(user__profile__lab_group=group_name)
    if grade_name != "all":
        logs = logs.filter(user__profile__grade=grade_name)

    trend_bucket = "hour" if range_name == "today" else "day"
    data = aggregate_dashboard(logs, trend_bucket=trend_bucket)
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
        "custom_start": request.GET.get("start", ""),
        "custom_end": request.GET.get("end", ""),
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


def _fetch_auth_files():
    """Fetch auth files from CPAP management API."""
    import requests as http_requests
    from urllib.parse import urljoin
    headers = {"Authorization": f"Bearer {settings.CLIPROXY_MANAGEMENT_KEY}"}
    resp = http_requests.get(
        urljoin(settings.CLIPROXY_MANAGEMENT_BASE_URL, "/v0/management/auth-files"),
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("files", []) if isinstance(data, dict) else data


def _fetch_kiro_quota(auth_index):
    """Fetch Kiro quota for a specific auth index."""
    import requests as http_requests
    from urllib.parse import urljoin
    headers = {"Authorization": f"Bearer {settings.CLIPROXY_MANAGEMENT_KEY}"}
    resp = http_requests.get(
        urljoin(settings.CLIPROXY_MANAGEMENT_BASE_URL, f"/v0/management/kiro-quota?auth_index={auth_index}"),
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


@admin_required
def admin_credentials(request):
    """Display all CPAP auth credentials grouped by provider."""
    from django.http import JsonResponse
    from collections import defaultdict

    try:
        files = _fetch_auth_files()
    except Exception as e:
        files = []
        from django.contrib import messages
        messages.error(request, f"获取凭证失败: {e}")

    # Group by provider
    grouped = defaultdict(list)
    for f in files:
        provider = f.get("provider", "unknown")
        # Extract useful info
        credential = {
            "auth_index": f.get("auth_index", ""),
            "email": f.get("email", f.get("account", "")),
            "provider": provider,
            "disabled": f.get("disabled", False),
            "failed": f.get("failed", 0),
            "success": f.get("success", 0),
            "recent_requests": f.get("recent_requests", []),
            "kiro_quota": f.get("kiro_quota"),
        }
        # Codex: extract plan info
        id_token = f.get("id_token", {})
        if id_token:
            credential["plan_type"] = id_token.get("plan_type", "")
            credential["subscription_until"] = id_token.get("chatgpt_subscription_active_until", "")
        grouped[provider].append(credential)

    # Sort providers
    provider_order = ["codex", "kiro", "gemini-cli", "antigravity"]
    sorted_groups = []
    for p in provider_order:
        if p in grouped:
            sorted_groups.append((p, grouped.pop(p)))
    for p, creds in sorted(grouped.items()):
        sorted_groups.append((p, creds))

    return render(request, "dashboard/credentials.html", {
        "credential_groups": sorted_groups,
        "total_count": len(files),
    })


@admin_required
def admin_credentials_refresh(request, auth_index):
    """AJAX endpoint to refresh Kiro quota for a credential."""
    from django.http import JsonResponse
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)
    try:
        quota = _fetch_kiro_quota(auth_index)
        return JsonResponse({"ok": True, "quota": quota})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
