from django.urls import path

from usage import views

urlpatterns = [
    path("my/", views.my_usage_logs, name="my-usage-logs"),
    path("summary/", views.usage_public_summary, name="usage-summary"),
    path("import/", views.import_usage_logs_view, name="import-usage-logs"),
    path("sync/status/", views.auto_sync_status, name="auto-sync-status"),
]
