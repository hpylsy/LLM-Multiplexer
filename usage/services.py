import csv
import json
import threading
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from urllib.parse import urljoin

import requests

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Max, Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from api_keys.models import APIKey
from dashboard.models import ModelPricing
from usage.models import UsageImportJob, UsageLog


SYNC_LOCK = threading.Lock()
LAST_SYNC_AT = 0.0
SYNC_INTERVAL_SECONDS = 60
DASHBOARD_RANK_LIMIT = 8

DEFAULT_MODEL_PRICING = {
    "gpt-5.4": (Decimal("2.50"), Decimal("15.00"), Decimal("0.25")),
    "gpt-5.5": (Decimal("5.00"), Decimal("30.00"), Decimal("0.50")),
    "gpt-5.3-codex": (Decimal("1.75"), Decimal("14.00"), Decimal("0.175")),
    "gpt-5.4-mini": (Decimal("0.75"), Decimal("4.50"), Decimal("0.075")),
    "gemini-3.1-pro-preview": (Decimal("2.00"), Decimal("12.00"), Decimal("0.20")),
    "gemini-3.1-flash-lite-preview": (Decimal("0.25"), Decimal("1.50"), Decimal("0.03")),
}


def get_model_pricing(model_name):
    pricing = ModelPricing.objects.filter(model_name=model_name).first()
    if pricing:
        return pricing.prompt_price_per_million, pricing.completion_price_per_million, pricing.cached_price_per_million
    return DEFAULT_MODEL_PRICING.get(model_name, (Decimal("0"), Decimal("0"), Decimal("0")))


def calculate_estimated_cost(model_name, prompt_tokens, completion_tokens, raw_payload=None):
    prompt_rate, completion_rate, cached_rate = get_model_pricing(model_name)
    raw_payload = raw_payload or {}
    cached_tokens = int(((raw_payload.get("tokens") or {}).get("cached_tokens") or raw_payload.get("cached_tokens") or 0))
    normal_prompt_tokens = max(int(prompt_tokens) - cached_tokens, 0)
    cost = (
        Decimal(normal_prompt_tokens) * prompt_rate
        + Decimal(completion_tokens) * completion_rate
        + Decimal(cached_tokens) * cached_rate
    ) / Decimal("1000000")
    return cost.quantize(Decimal("0.000001"))


def parse_request_time(value):
    if not value:
        return timezone.now()
    if isinstance(value, datetime):
        return value
    parsed = parse_datetime(str(value))
    if parsed:
        return parsed if timezone.is_aware(parsed) else timezone.make_aware(parsed)
    return timezone.now()


def normalize_usage_record(record):
    prompt_tokens = int(record.get("prompt_tokens") or 0)
    completion_tokens = int(record.get("completion_tokens") or 0)
    total_tokens = int(record.get("total_tokens") or prompt_tokens + completion_tokens)
    estimated_cost_raw = record.get("estimated_cost")
    if estimated_cost_raw in (None, "", 0, "0"):
        estimated_cost = calculate_estimated_cost(str(record.get("model_name") or "unknown").strip(), prompt_tokens, completion_tokens, record)
    else:
        estimated_cost = Decimal(str(estimated_cost_raw))
    status_code = int(record.get("status_code") or 200)
    error_message = record.get("error_message") or ""
    return {
        "request_id": str(record.get("request_id") or "").strip(),
        "user_identifier": str(record.get("user_identifier") or "").strip(),
        "api_key_identifier": str(record.get("api_key_identifier") or "").strip(),
        "model_name": str(record.get("model_name") or "unknown").strip(),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": estimated_cost,
        "status_code": status_code,
        "is_error": status_code >= 400 or bool(error_message),
        "error_message": error_message,
        "request_time": parse_request_time(record.get("request_time")),
        "raw_payload": record,
    }


def resolve_related_objects(data):
    user = None
    api_key = None
    if data["user_identifier"]:
        user = User.objects.filter(Q(username=data["user_identifier"]) | Q(email=data["user_identifier"])).first()
    if data["api_key_identifier"]:
        token_value = data["api_key_identifier"].strip()
        api_key = APIKey.objects.filter(
            Q(token_hash=APIKey.hash_token(token_value))
            | Q(token_prefix__iexact=token_value)
            | Q(token_masked__iexact=token_value)
            | Q(name__iexact=token_value)
        ).select_related("user").first()
        if api_key and not user:
            user = api_key.user
    return user, api_key


def import_usage_records(records, source_type, source_name):
    job = UsageImportJob.objects.create(source_type=source_type, source_name=source_name)
    imported = skipped = failed = 0
    errors = []

    # Quick pre-filter: extract request_ids first (cheap) and batch check existence
    raw_request_ids = []
    for raw in records:
        rid = str(raw.get("request_id") or "").strip()
        if rid:
            raw_request_ids.append(rid)

    # Batch lookup in chunks of 500 to avoid overly large IN clauses
    existing_ids = set()
    for i in range(0, len(raw_request_ids), 500):
        chunk = raw_request_ids[i:i + 500]
        existing_ids.update(
            UsageLog.objects.filter(request_id__in=chunk).values_list("request_id", flat=True)
        )

    # Only normalize and import records that are actually new
    for index, raw in enumerate(records, start=1):
        try:
            rid = str(raw.get("request_id") or "").strip()
            if not rid:
                failed += 1
                errors.append(f"第 {index} 行缺少 request_id")
                continue
            if rid in existing_ids:
                skipped += 1
                continue
            # Only do expensive normalization for new records
            data = normalize_usage_record(raw)
            user, api_key = resolve_related_objects(data)
            UsageLog.objects.create(**data, user=user, api_key=api_key)
            existing_ids.add(rid)  # Prevent duplicates within same batch
            imported += 1
        except Exception as exc:
            failed += 1
            errors.append(f"第 {index} 行导入失败: {exc}")
            errors.append(f"第 {index} 行导入失败: {exc}")

    job.imported_count = imported
    job.skipped_count = skipped
    job.failed_count = failed
    job.summary = "\n".join(errors[:20])
    job.save(update_fields=["imported_count", "skipped_count", "failed_count", "summary"])
    return job


def fetch_cliproxy_usage_records():
    headers = {"Authorization": f"Bearer {settings.CLIPROXY_MANAGEMENT_KEY}"}
    response = requests.get(
        urljoin(settings.CLIPROXY_MANAGEMENT_BASE_URL, "/v0/management/usage"),
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def normalize_cliproxy_usage_payload(payload):
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        raise ValueError("cliproxy usage 返回格式无效")

    for key in ["items", "data", "usage", "records"]:
        if isinstance(payload.get(key), list):
            return payload[key]

    usage_block = payload.get("usage") or {}
    apis = usage_block.get("apis") or {}
    records = []

    for api_key_identifier, api_item in apis.items():
        models = api_item.get("models") or {}
        for model_name, model_item in models.items():
            for detail in model_item.get("details") or []:
                token_info = detail.get("tokens") or {}
                records.append(
                    {
                        "request_id": detail.get("request_id") or f"cliproxy-{api_key_identifier[:12]}-{model_name}-{detail.get('timestamp')}",
                        "user_identifier": detail.get("source") or "",
                        "api_key_identifier": api_key_identifier,
                        "model_name": model_name,
                        "prompt_tokens": token_info.get("input_tokens") or 0,
                        "completion_tokens": token_info.get("output_tokens") or 0,
                        "total_tokens": token_info.get("total_tokens") or 0,
                        "estimated_cost": detail.get("estimated_cost") or detail.get("cost") or 0,
                        "status_code": 500 if detail.get("failed") else 200,
                        "error_message": detail.get("error_message") or "",
                        "request_time": detail.get("timestamp"),
                        "raw_payload": detail,
                    }
                )

    return records


def sync_cliproxy_usage_records():
    payload = fetch_cliproxy_usage_records()
    records = normalize_cliproxy_usage_payload(payload)

    # Only import records whose api_key_identifier matches a key bound in the portal.
    # This filters out usage from external/outsourced keys not managed here.
    known_plaintexts = set(
        APIKey.objects.exclude(token_plaintext="").values_list("token_plaintext", flat=True)
    )
    known_hashes = set(
        APIKey.objects.values_list("token_hash", flat=True)
    )
    known_prefixes = set(
        APIKey.objects.exclude(token_prefix="").values_list("token_prefix", flat=True)
    )

    filtered = []
    for record in records:
        key_id = (record.get("api_key_identifier") or "").strip()
        if not key_id:
            # No key identifier — include it (might be matched by user_identifier later)
            filtered.append(record)
            continue
        if key_id in known_plaintexts:
            filtered.append(record)
        elif APIKey.hash_token(key_id) in known_hashes:
            filtered.append(record)
        elif key_id[:12] in known_prefixes:
            filtered.append(record)
        # else: external key, skip

    return import_usage_records(filtered, UsageImportJob.SOURCE_API, "cliproxy-management-api")


def auto_sync_cliproxy_usage_records(force=False):
    global LAST_SYNC_AT
    now = time.time()
    if not force and now - LAST_SYNC_AT < SYNC_INTERVAL_SECONDS:
        latest_job = UsageImportJob.objects.filter(source_name="cliproxy-management-api").first()
        return latest_job, False

    if not SYNC_LOCK.acquire(blocking=False):
        latest_job = UsageImportJob.objects.filter(source_name="cliproxy-management-api").first()
        return latest_job, False

    try:
        job = sync_cliproxy_usage_records()
        LAST_SYNC_AT = time.time()
        return job, True
    finally:
        SYNC_LOCK.release()


def fetch_usage_queue_events(count=100):
    """Consume real-time events from CPAP /v0/management/usage-queue endpoint."""
    headers = {"Authorization": f"Bearer {settings.CLIPROXY_MANAGEMENT_KEY}"}
    response = requests.get(
        urljoin(settings.CLIPROXY_MANAGEMENT_BASE_URL, f"/v0/management/usage-queue?count={count}"),
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def normalize_queue_event(event):
    """Normalize a single usage-queue event into UsageLog-compatible dict."""
    tokens = event.get("tokens") or {}
    input_tokens = int(tokens.get("input_tokens") or 0)
    output_tokens = int(tokens.get("output_tokens") or 0)
    cached_tokens = int(tokens.get("cached_tokens") or 0)
    reasoning_tokens = int(tokens.get("reasoning_tokens") or 0)
    total_tokens = int(tokens.get("total_tokens") or input_tokens + output_tokens)
    model_name = str(event.get("model") or event.get("alias") or "unknown").strip()
    failed = bool(event.get("failed"))

    estimated_cost = calculate_estimated_cost(model_name, input_tokens, output_tokens, event)

    return {
        "request_id": str(event.get("request_id") or "").strip(),
        "user_identifier": str(event.get("source") or "").strip(),
        "api_key_identifier": str(event.get("api_key") or "").strip(),
        "model_name": model_name,
        "prompt_tokens": input_tokens,
        "completion_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": estimated_cost,
        "status_code": 500 if failed else 200,
        "is_error": failed,
        "error_message": "",
        "request_time": parse_request_time(event.get("timestamp")),
        "raw_payload": event,
        "latency_ms": int(event.get("latency_ms") or 0),
        "cached_tokens": cached_tokens,
        "reasoning_tokens": reasoning_tokens,
        "provider": str(event.get("provider") or "").strip(),
    }


QUEUE_SYNC_LOCK = threading.Lock()
LAST_QUEUE_SYNC_AT = 0.0
QUEUE_SYNC_INTERVAL_SECONDS = 30


def sync_usage_queue_events(count=100):
    """Fetch and persist events from the usage-queue, deduplicating by request_id."""
    payload = fetch_usage_queue_events(count)

    # The endpoint may return a list or a dict with a list inside
    if isinstance(payload, list):
        events = payload
    elif isinstance(payload, dict):
        events = payload.get("items") or payload.get("data") or payload.get("messages") or []
    else:
        events = []

    if not events:
        return 0, 0

    # Extract request_ids for batch dedup check
    raw_ids = [str(e.get("request_id") or "").strip() for e in events if e.get("request_id")]
    existing_ids = set()
    for i in range(0, len(raw_ids), 500):
        chunk = raw_ids[i:i + 500]
        existing_ids.update(
            UsageLog.objects.filter(request_id__in=chunk).values_list("request_id", flat=True)
        )

    imported = 0
    skipped = 0
    for event in events:
        rid = str(event.get("request_id") or "").strip()
        if not rid:
            skipped += 1
            continue
        if rid in existing_ids:
            skipped += 1
            continue

        data = normalize_queue_event(event)
        user, api_key = resolve_related_objects(data)
        UsageLog.objects.create(**data, user=user, api_key=api_key)
        existing_ids.add(rid)
        imported += 1

    return imported, skipped


def auto_sync_usage_queue(force=False):
    """Auto-sync usage queue events with rate limiting (every 30s)."""
    global LAST_QUEUE_SYNC_AT
    now = time.time()
    if not force and now - LAST_QUEUE_SYNC_AT < QUEUE_SYNC_INTERVAL_SECONDS:
        return None, False

    if not QUEUE_SYNC_LOCK.acquire(blocking=False):
        return None, False

    try:
        imported, skipped = sync_usage_queue_events()
        LAST_QUEUE_SYNC_AT = time.time()
        return {"imported": imported, "skipped": skipped}, True
    except Exception:
        return None, False
    finally:
        QUEUE_SYNC_LOCK.release()


def load_records_from_file(uploaded_file):
    name = uploaded_file.name.lower()
    content = uploaded_file.read().decode("utf-8")
    if name.endswith(".jsonl"):
        return [json.loads(line) for line in content.splitlines() if line.strip()]
    if name.endswith(".csv"):
        reader = csv.DictReader(content.splitlines())
        return list(reader)
    raise ValueError("仅支持 CSV 或 JSONL 文件")


def mask_username(name, enabled=True, index=None):
    if not enabled:
        return name
    if index is not None:
        return f"user_{index:02d}"
    if len(name) <= 1:
        return "*"
    return f"{name[0]}*"


def _preferred_display_name(display_name, username, fallback="未设置显示名"):
    value = (display_name or "").strip()
    username_value = (username or "").strip()
    if value and value.lower() != username_value.lower():
        return value
    return fallback


def _payload_int(payload, *paths):
    payload = payload or {}
    for path in paths:
        value = payload
        for key in path:
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(key)
        if value not in (None, ""):
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return 0


def _trend_label(request_time, trend_bucket):
    local_time = timezone.localtime(request_time)
    if trend_bucket == "hour":
        return local_time.replace(minute=0, second=0, microsecond=0).strftime("%H:%M")
    return local_time.date().isoformat()


def aggregate_dashboard(queryset, trend_bucket="day"):
    total_requests = queryset.count()
    summary = queryset.aggregate(total_tokens=Sum("total_tokens"), total_cost=Sum("estimated_cost"), error_count=Count("id", filter=Q(is_error=True)))
    total_tokens = summary["total_tokens"] or 0
    total_cost = summary["total_cost"] or Decimal("0")
    error_count = summary["error_count"] or 0
    error_rate = round((error_count / total_requests) * 100, 2) if total_requests else 0
    active_users = queryset.exclude(user=None).values("user").distinct().count()
    active_keys = queryset.exclude(api_key=None).values("api_key").distinct().count()
    model_rank = list(
        queryset.values("model_name")
        .annotate(total_requests=Count("id"), total_tokens=Sum("total_tokens"))
        .order_by("-total_tokens", "-total_requests")[:10]
    )
    error_model_rank = list(
        queryset.filter(is_error=True)
        .values("model_name")
        .annotate(total_errors=Count("id"), total_tokens=Sum("total_tokens"))
        .order_by("-total_errors", "-total_tokens")[:10]
    )
    user_rank = list(
        queryset.exclude(user=None)
        .filter(user__profile__is_dashboard_visible=True)
        .values("user", "user__username", "user__profile__display_name", "user__profile__lab_group", "user__profile__grade")
        .annotate(total_tokens=Sum("total_tokens"))
        .order_by("-total_tokens")[:DASHBOARD_RANK_LIMIT]
    )
    key_rank = []
    top_keys = list(
        queryset.exclude(api_key=None)
        .filter(api_key__user__profile__is_dashboard_visible=True)
        .values("api_key", "api_key__user__username", "api_key__user__profile__display_name", "api_key__user__profile__lab_group", "api_key__user__profile__grade")
        .annotate(total_tokens=Sum("total_tokens"), total_requests=Count("id"), top_model=Max("model_name"))
        .order_by("-total_tokens")
    )
    for item in top_keys:
        key_rank.append(
            {
                "display_name": _preferred_display_name(item["api_key__user__profile__display_name"], item["api_key__user__username"]),
                "group_name": item["api_key__user__profile__lab_group"] or "未分组",
                "grade": item["api_key__user__profile__grade"] or "未设置",
                "top_model": item["top_model"],
                "total_tokens": item["total_tokens"],
                "total_requests": item["total_requests"],
            }
        )
    # Use DB-level aggregation for trend data to avoid loading all rows into memory
    from django.db.models.functions import TruncHour, TruncDate
    trunc_fn = TruncHour if trend_bucket == "hour" else TruncDate
    trend_qs = (
        queryset
        .annotate(bucket=trunc_fn("request_time"))
        .values("bucket")
        .annotate(
            tokens=Sum("total_tokens"),
            prompt_tokens=Sum("prompt_tokens"),
            completion_tokens=Sum("completion_tokens"),
            requests=Count("id"),
            errors=Count("id", filter=Q(is_error=True)),
        )
        .order_by("bucket")
    )
    # For cached/thinking tokens we still need raw_payload parsing on a limited set
    trend_map = defaultdict(lambda: {"tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "cached_tokens": 0, "thinking_tokens": 0, "requests": 0, "errors": 0})
    for row in trend_qs:
        if row["bucket"] is None:
            continue
        bucket = row["bucket"]
        if trend_bucket == "hour":
            local_time = timezone.localtime(bucket)
            label = local_time.strftime("%H:%M")
        else:
            # TruncDate returns a date object, not datetime
            label = bucket.isoformat() if hasattr(bucket, 'isoformat') else str(bucket)
        trend_map[label]["tokens"] += row["tokens"] or 0
        trend_map[label]["prompt_tokens"] += row["prompt_tokens"] or 0
        trend_map[label]["completion_tokens"] += row["completion_tokens"] or 0
        trend_map[label]["requests"] += row["requests"] or 0
        trend_map[label]["errors"] += row["errors"] or 0

    # Parse cached/thinking tokens from raw_payload (only fetch needed fields)
    for row in queryset.only("request_time", "raw_payload").iterator(chunk_size=500):
        label = _trend_label(row.request_time, trend_bucket)
        cached_tokens = _payload_int(row.raw_payload, ("raw_payload", "tokens", "cached_tokens"), ("tokens", "cached_tokens"), ("cached_tokens",), ("usage", "cached_tokens"))
        thinking_tokens = _payload_int(
            row.raw_payload,
            ("raw_payload", "tokens", "reasoning_tokens"),
            ("raw_payload", "tokens", "thinking_tokens"),
            ("tokens", "thinking_tokens"),
            ("tokens", "reasoning_tokens"),
            ("thinking_tokens",),
            ("reasoning_tokens",),
            ("usage", "thinking_tokens"),
            ("usage", "reasoning_tokens"),
            ("completion_tokens_details", "reasoning_tokens"),
        )
        if cached_tokens or thinking_tokens:
            trend_map[label]["cached_tokens"] += cached_tokens
            trend_map[label]["thinking_tokens"] += thinking_tokens

    trend = [{"date": label, **values, "error_rate": round((values['errors'] / values['requests']) * 100, 2) if values['requests'] else 0} for label, values in trend_map.items()]
    recent_errors = list(
        queryset.filter(is_error=True)
        .exclude(user=None)
        .select_related("user", "api_key", "user__profile")[:30]
    )
    recent_active_users = list(
        queryset.exclude(user=None)
        .values("user__username", "user__profile__display_name")
        .annotate(last_time=Sum("total_tokens"))
        .order_by("-last_time")[:10]
    )
    return {
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "error_rate": error_rate,
        "active_users": active_users,
        "active_keys": active_keys,
        "model_rank": model_rank,
        "error_model_rank": error_model_rank,
        "user_rank": user_rank,
        "key_rank": key_rank,
        "trend": trend,
        "recent_errors": recent_errors,
        "recent_active_users": recent_active_users,
    }
