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


def _cpap_api_call(auth_index, method, url, extra_headers=None):
    """Call an external API through CPAP using a specific credential's token."""
    import requests as http_requests
    from urllib.parse import urljoin
    headers = {"Authorization": f"Bearer {settings.CLIPROXY_MANAGEMENT_KEY}"}
    payload = {
        "auth_index": auth_index,
        "method": method,
        "url": url,
    }
    if extra_headers:
        payload["header"] = extra_headers
    resp = http_requests.post(
        urljoin(settings.CLIPROXY_MANAGEMENT_BASE_URL, "/v0/management/api-call"),
        headers=headers,
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


# Quota API configs per provider (same as cpa-usage-keeper)
QUOTA_CONFIGS = {
    "codex": {
        "method": "GET",
        "url": "https://chatgpt.com/backend-api/wham/usage",
        "headers": {"Content-Type": "application/json", "User-Agent": "codex_cli_rs/0.76.0 (Debian 13.0.0; x86_64) WindowsTerminal"},
    },
    "gemini-cli": {
        "method": "POST",
        "url": "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuota",
        "headers": {"Content-Type": "application/json"},
    },
    "antigravity": {
        "method": "POST",
        "url": "https://daily-cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels",
        "headers": {"Content-Type": "application/json", "User-Agent": "antigravity/1.11.5 windows/amd64"},
    },
}


def _parse_codex_quota(data):
    """Parse Codex quota response into normalized format."""
    body = data.get("body", "")
    if isinstance(body, str):
        import json as json_mod
        try:
            body = json_mod.loads(body)
        except (ValueError, TypeError):
            return None
    if not isinstance(body, dict):
        return None

    rate_limit = body.get("rate_limit") or body.get("rateLimit") or {}
    result = {"provider": "codex", "plan_type": body.get("plan_type", ""), "windows": []}

    for key, label in [("primary_window", "5h"), ("secondary_window", "Weekly"), ("primaryWindow", "5h"), ("secondaryWindow", "Weekly")]:
        window = rate_limit.get(key)
        if window:
            result["windows"].append({
                "label": label,
                "used_percent": window.get("used_percent", window.get("usedPercent", 0)),
                "reset_after_seconds": window.get("reset_after_seconds", window.get("resetAfterSeconds", 0)),
                "limit_reached": window.get("limit_reached", window.get("limitReached", False)),
            })

    # Also check additional rate limits
    for item in body.get("additional_rate_limits", body.get("additionalRateLimits", [])):
        rl = item.get("rate_limit", item.get("rateLimit", {}))
        for key, label in [("primary_window", "5h"), ("secondary_window", "Weekly")]:
            window = rl.get(key, rl.get(key.replace("_", ""), None))
            if window:
                result["windows"].append({
                    "label": f"{item.get('limit_name', item.get('limitName', ''))}/{label}",
                    "used_percent": window.get("used_percent", window.get("usedPercent", 0)),
                    "reset_after_seconds": window.get("reset_after_seconds", window.get("resetAfterSeconds", 0)),
                    "limit_reached": window.get("limit_reached", window.get("limitReached", False)),
                })

    return result if result["windows"] else None


def _parse_gemini_quota(data):
    """Parse Gemini CLI quota response."""
    body = data.get("body", "")
    if isinstance(body, str):
        import json as json_mod
        try:
            body = json_mod.loads(body)
        except (ValueError, TypeError):
            return None
    if not isinstance(body, dict):
        return None

    result = {"provider": "gemini-cli", "windows": []}
    for bucket in body.get("buckets", []):
        remaining = bucket.get("remainingFraction", bucket.get("remaining_fraction", 0))
        result["windows"].append({
            "label": bucket.get("modelId", bucket.get("model_id", "unknown")),
            "used_percent": round((1 - remaining) * 100, 1) if remaining else 0,
            "reset_after_seconds": 0,
            "remaining_fraction": remaining,
        })
    return result if result["windows"] else None


@login_required
def admin_credentials(request):
    """Display all CPAP auth credentials grouped by provider."""
    from collections import defaultdict
    from datetime import timedelta
    from django.utils import timezone as tz

    try:
        files = _fetch_auth_files()
    except Exception as e:
        files = []
        from django.contrib import messages
        messages.error(request, f"获取凭证失败: {e}")

    now = tz.now()

    # Group by provider
    grouped = defaultdict(list)
    for f in files:
        provider = f.get("provider", "unknown")
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
        # Codex: extract plan info and calculate remaining subscription days
        id_token = f.get("id_token") or {}
        if id_token:
            credential["plan_type"] = id_token.get("plan_type", "")
            sub_until = id_token.get("chatgpt_subscription_active_until", "")
            credential["subscription_until"] = sub_until
            if sub_until:
                from django.utils.dateparse import parse_datetime as pd
                end = pd(sub_until)
                if end:
                    days_left = (end - now).days
                    credential["days_left"] = max(days_left, 0)

        # Calculate 5h and weekly usage from recent_requests
        recent = f.get("recent_requests") or []
        # Each slot is 10 min, 5h = 30 slots, weekly ~= all available slots
        five_h_slots = recent[-30:] if len(recent) >= 30 else recent
        weekly_slots = recent

        five_h_success = sum(s.get("success", 0) for s in five_h_slots)
        five_h_failed = sum(s.get("failed", 0) for s in five_h_slots)
        weekly_success = sum(s.get("success", 0) for s in weekly_slots)
        weekly_failed = sum(s.get("failed", 0) for s in weekly_slots)

        credential["five_h_total"] = five_h_success + five_h_failed
        credential["five_h_success"] = five_h_success
        credential["five_h_failed"] = five_h_failed
        credential["weekly_total"] = weekly_success + weekly_failed
        credential["weekly_success"] = weekly_success
        credential["weekly_failed"] = weekly_failed

        # Progress bar percentages (estimate max capacity)
        # Codex Plus: ~50 req/5h, ~500 req/week; Team: ~100/5h, ~1000/week
        plan = (id_token.get("plan_type", "") if id_token else "").lower()
        five_h_cap = 100 if plan == "team" else 50
        weekly_cap = 1000 if plan == "team" else 500
        if provider == "kiro":
            five_h_cap, weekly_cap = 30, 200
        elif provider in ("gemini-cli", "antigravity"):
            five_h_cap, weekly_cap = 80, 600

        credential["five_h_pct"] = min(round(five_h_success / five_h_cap * 100), 100) if five_h_cap else 0
        credential["five_h_fail_pct"] = min(round(five_h_failed / five_h_cap * 100), 100 - credential["five_h_pct"]) if five_h_cap else 0
        credential["weekly_pct"] = min(round(weekly_success / weekly_cap * 100), 100) if weekly_cap else 0
        credential["weekly_fail_pct"] = min(round(weekly_failed / weekly_cap * 100), 100 - credential["weekly_pct"]) if weekly_cap else 0

        # Labels: show time info from first/last slot
        if five_h_slots:
            credential["five_h_label"] = f"{five_h_success + five_h_failed}req ({five_h_slots[0].get('time', '')})"
        else:
            credential["five_h_label"] = "0req"
        if weekly_slots:
            credential["weekly_label"] = f"{weekly_success + weekly_failed}req ({weekly_slots[-1].get('time', '')})"
        else:
            credential["weekly_label"] = "0req"

        # Email masking for non-admin users
        email = credential["email"]
        if email and not request.user.is_staff:
            parts = email.split("@")
            if len(parts) == 2:
                name = parts[0]
                masked_name = name[:3] + "***" if len(name) > 3 else name[0] + "***"
                credential["email_masked"] = f"{masked_name}@{parts[1]}"
            else:
                credential["email_masked"] = email[:4] + "***"
        else:
            credential["email_masked"] = email

        # Determine health status
        if f.get("disabled"):
            credential["health"] = "disabled"
        elif f.get("failed", 0) > 0 and f.get("success", 0) == 0:
            credential["health"] = "error"
        elif f.get("failed", 0) > 0:
            credential["health"] = "warning"
        else:
            credential["health"] = "healthy"

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


@login_required
def admin_credentials_refresh(request, auth_index):
    """AJAX endpoint to refresh quota for a credential."""
    from django.http import JsonResponse
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)

    import json as json_mod
    provider = request.POST.get("provider", request.GET.get("provider", ""))

    try:
        if provider == "kiro":
            # Use dedicated kiro-quota endpoint
            import requests as http_requests
            from urllib.parse import urljoin
            headers = {"Authorization": f"Bearer {settings.CLIPROXY_MANAGEMENT_KEY}"}
            resp = http_requests.get(
                urljoin(settings.CLIPROXY_MANAGEMENT_BASE_URL, f"/v0/management/kiro-quota?auth_index={auth_index}"),
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            return JsonResponse({"ok": True, "quota": resp.json(), "provider": "kiro"})

        elif provider in QUOTA_CONFIGS:
            config = QUOTA_CONFIGS[provider]
            data = _cpap_api_call(auth_index, config["method"], config["url"], config.get("headers"))

            if provider == "codex":
                parsed = _parse_codex_quota(data)
            elif provider == "gemini-cli":
                parsed = _parse_gemini_quota(data)
            else:
                parsed = {"provider": provider, "raw": data}

            if parsed:
                return JsonResponse({"ok": True, "quota": parsed, "provider": provider})
            else:
                return JsonResponse({"ok": False, "error": "无法解析配额数据", "raw_status": data.get("status_code")})
        else:
            return JsonResponse({"ok": False, "error": f"不支持的 provider: {provider}"})

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
