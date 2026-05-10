from django.urls import path

from dashboard import views

urlpatterns = [
    path("public/", views.public_dashboard, name="public-dashboard"),
    path("admin/", views.admin_dashboard, name="admin-dashboard"),
    path("admin/pricing/", views.model_pricing_admin, name="admin-model-pricing"),
]
