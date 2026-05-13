from datetime import timedelta
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from core.utils import admin_required
from usage.forms import UsageLogUploadForm
from usage.models import UsageImportJob, UsageLog
from usage.services import auto_sync_cliproxy_usage_records, auto_sync_usage_queue, import_usage_records, load_records_from_file, sync_cliproxy_usage_records


@login_required
def my_usage_logs(request):
    range_name = request.GET.get("range", "today")
    now = timezone.localtime()
    if range_name == "this_month":
        chart_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif range_name == "last_7_days":
        chart_start = now - timedelta(days=7)
    elif range_name == "last_30_days":
        chart_start = now - timedelta(days=30)
    elif range_name == "all":
        chart_start = None
    else:
        range_name = "today"
        chart_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    logs = UsageLog.objects.filter(user=request.user).select_related("api_key")[:100]
    chart_logs = UsageLog.objects.filter(user=request.user)
    if chart_start:
        chart_logs = chart_logs.filter(request_time__gte=chart_start)

    model_usage = list(
        chart_logs
        .values("model_name")
        .annotate(total_tokens=Sum("total_tokens"))
        .order_by("-total_tokens")
    )

    # Build token type trend data (same as dashboard)
    from usage.services import _payload_int
    trend_map = defaultdict(lambda: {"tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0, "thinking_tokens": 0})
    for item in chart_logs.only("request_time", "prompt_tokens", "completion_tokens", "total_tokens", "raw_payload").order_by("request_time"):
        local_time = timezone.localtime(item.request_time)
        if range_name == "today":
            label = local_time.strftime("%H:00")
        else:
            label = local_time.date().isoformat()
        trend_map[label]["tokens"] += item.total_tokens
        trend_map[label]["prompt_tokens"] += item.prompt_tokens
        trend_map[label]["completion_tokens"] += item.completion_tokens
        cached = _payload_int(item.raw_payload, ("raw_payload", "tokens", "cached_tokens"), ("tokens", "cached_tokens"), ("cached_tokens",))
        thinking = _payload_int(item.raw_payload, ("raw_payload", "tokens", "reasoning_tokens"), ("raw_payload", "tokens", "thinking_tokens"), ("tokens", "reasoning_tokens"))
        trend_map[label]["cached_tokens"] += cached
        trend_map[label]["thinking_tokens"] += thinking

    # Fill empty hours for today view
    if range_name == "today":
        for hour in range(24):
            key = f"{hour:02d}:00"
            if key not in trend_map:
                trend_map[key] = {"tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0, "thinking_tokens": 0}

    trend_data = [{"date": label, **values} for label, values in sorted(trend_map.items())]

    return render(request, "usage/my_usage_logs.html", {
        "logs": logs,
        "trend_data": trend_data,
        "model_usage": model_usage,
        "range_name": range_name,
    })


@admin_required
def import_usage_logs_view(request):
    if request.method == "POST":
        if "sync_cliproxy" in request.POST:
            job = sync_cliproxy_usage_records()
            messages.success(request, f"CLIProxy 同步完成：成功 {job.imported_count}，跳过 {job.skipped_count}，失败 {job.failed_count}")
            return redirect("import-usage-logs")
        form = UsageLogUploadForm(request.POST, request.FILES)
        if form.is_valid():
            records = load_records_from_file(form.cleaned_data["source_file"])
            job = import_usage_records(records, UsageImportJob.SOURCE_UPLOAD, form.cleaned_data["source_file"].name)
            messages.success(request, f"导入完成：成功 {job.imported_count}，跳过 {job.skipped_count}，失败 {job.failed_count}")
            return redirect("import-usage-logs")
    else:
        form = UsageLogUploadForm()
    jobs = UsageImportJob.objects.all()[:20]
    return render(request, "usage/import_usage_logs.html", {"form": form, "jobs": jobs})


@admin_required
def sync_trigger(request):
    """AJAX endpoint for manual sync trigger."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)
    try:
        job = sync_cliproxy_usage_records()
        return JsonResponse({
            "ok": True,
            "imported": job.imported_count,
            "skipped": job.skipped_count,
            "failed": job.failed_count,
        })
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@login_required
def auto_sync_status(request):
    job, triggered = auto_sync_cliproxy_usage_records()
    return JsonResponse(
        {
            "ok": True,
            "triggered": triggered,
            "job": {
                "imported_count": getattr(job, "imported_count", 0),
                "skipped_count": getattr(job, "skipped_count", 0),
                "failed_count": getattr(job, "failed_count", 0),
                "created_at": job.created_at.isoformat() if job else None,
            },
        }
    )


@login_required
def usage_public_summary(request):
    days = request.GET.get("range", "7")
    try:
        days = int(days)
    except ValueError:
        days = 7
    start = timezone.now() - timedelta(days=days)
    logs = UsageLog.objects.filter(request_time__gte=start)
    if not request.user.is_staff:
        logs = logs.filter(user=request.user)
    return render(request, "usage/usage_public_summary.html", {"logs": logs[:50], "public_dashboard_enabled": settings.PUBLIC_DASHBOARD_ENABLED})


@login_required
def request_events(request):
    """Request events page - shows real-time API request details."""
    # Trigger queue sync on page load
    auto_sync_usage_queue()

    # Filters
    range_name = request.GET.get("range", "today")
    provider_filter = request.GET.get("provider", "").strip()
    model_filter = request.GET.get("model", "").strip()

    now = timezone.localtime()
    if range_name == "last_hour":
        start = now - timedelta(hours=1)
    elif range_name == "last_7_days":
        start = now - timedelta(days=7)
    elif range_name == "last_30_days":
        start = now - timedelta(days=30)
    elif range_name == "all":
        start = None
    else:
        range_name = "today"
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    qs = UsageLog.objects.all().order_by("-request_time")
    if start:
        qs = qs.filter(request_time__gte=start)
    if provider_filter:
        qs = qs.filter(provider=provider_filter)
    if model_filter:
        qs = qs.filter(model_name__icontains=model_filter)

    # Pagination
    paginator = Paginator(qs, 50)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Get distinct providers and models for filter dropdowns
    providers = list(
        UsageLog.objects.exclude(provider="")
        .values_list("provider", flat=True)
        .distinct()
        .order_by("provider")
    )
    models_list = list(
        UsageLog.objects.values_list("model_name", flat=True)
        .distinct()
        .order_by("model_name")
    )

    # Determine if user is admin (for masking)
    is_admin = request.user.is_staff or getattr(getattr(request.user, "profile", None), "role", "") == "admin"

    context = {
        "page_obj": page_obj,
        "range_name": range_name,
        "provider_filter": provider_filter,
        "model_filter": model_filter,
        "providers": providers,
        "models_list": models_list,
        "is_admin": is_admin,
    }
    return render(request, "usage/request_events.html", context)


@login_required
def request_events_sync(request):
    """AJAX endpoint to trigger usage-queue sync."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)
    try:
        result, triggered = auto_sync_usage_queue(force=True)
        if result:
            return JsonResponse({"ok": True, "triggered": triggered, **result})
        return JsonResponse({"ok": True, "triggered": False, "imported": 0, "skipped": 0})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
