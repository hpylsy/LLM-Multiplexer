from datetime import date

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from api_keys.models import APIKey
from quota.models import UserQuotaSnapshot


@login_required
def my_quota(request):
    today = date.today()
    snapshot = UserQuotaSnapshot.objects.filter(user=request.user, year=today.year, month=today.month).first()
    snapshots = UserQuotaSnapshot.objects.filter(user=request.user)[:12]
    bound_keys = APIKey.objects.filter(user=request.user, status=APIKey.STATUS_ACTIVE).order_by("-created_at")
    return render(request, "quota/my_quota.html", {"snapshot": snapshot, "snapshots": snapshots, "bound_keys": bound_keys, "cliproxy_base_url": f"{settings.CLIPROXY_BASE_URL.rstrip('/')}/v1"})
