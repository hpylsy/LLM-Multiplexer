from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("core.urls")),
    path("users/", include("users.urls")),
    path("keys/", include("api_keys.urls")),
    path("usage/", include("usage.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("quota/", include("quota.urls")),
    path("posts/", include("github_activity.urls")),
]
