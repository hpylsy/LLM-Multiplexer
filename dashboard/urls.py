from django.urls import path

from dashboard import views

urlpatterns = [
    path("public/", views.public_dashboard, name="public-dashboard"),
    path("admin/", views.admin_dashboard, name="admin-dashboard"),
    path("admin/pricing/", views.model_pricing_admin, name="admin-model-pricing"),
    path("admin/credentials/", views.admin_credentials, name="admin-credentials"),
    path("admin/credentials/refresh/<str:auth_index>/", views.admin_credentials_refresh, name="admin-credentials-refresh"),
]
