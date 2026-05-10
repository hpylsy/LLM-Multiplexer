from datetime import timedelta
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from core.utils import admin_required
from usage.forms import UsageLogUploadForm
from usage.models import UsageImportJob, UsageLog
from usage.services import auto_sync_cliproxy_usage_records, import_usage_records, load_records_from_file, sync_cliproxy_usage_records


@login_required
def my_usage_logs(request):
    range_name = request.GET.get("range", "today")
    now = timezone.localtime()
    if range_name == "this_month":
        chart_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif range_name == "last_7_days":
        chart_start = now - timedelta(days=7)
    else:
        range_name = "today"
        chart_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    logs = UsageLog.objects.filter(user=request.user).select_related("api_key")[:100]
    chart_logs = UsageLog.objects.filter(user=request.user, request_time__gte=chart_start)
    daily_usage_map = defaultdict(int)
    if range_name == "today":
        for hour in range(24):
            daily_usage_map[f"{hour:02d}:00"] = 0
    model_usage = list(
        chart_logs
        .values("model_name")
        .annotate(total_tokens=Sum("total_tokens"))
        .order_by("-total_tokens")
    )
    for item in chart_logs.order_by("request_time"):
        local_time = timezone.localtime(item.request_time)
        if range_name == "today":
            label = local_time.strftime("%H:00")
        else:
            label = local_time.date().isoformat()
        daily_usage_map[label] += item.total_tokens
    daily_usage = [{"date": day, "tokens": tokens} for day, tokens in daily_usage_map.items()]
    return render(request, "usage/my_usage_logs.html", {"logs": logs, "daily_usage": daily_usage, "model_usage": model_usage, "range_name": range_name})


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
