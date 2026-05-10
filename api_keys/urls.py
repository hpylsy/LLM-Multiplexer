from django.urls import path

from api_keys import views

urlpatterns = [
    path("my/", views.api_key_list, name="my-api-keys"),
    path("request/", views.api_key_request_create, name="request-api-key"),
    path("admin/list/", views.admin_api_key_list, name="admin-api-key-list"),
    path("admin/create/<int:user_id>/", views.admin_api_key_create, name="admin-api-key-create"),
    path("admin/<int:key_id>/edit/", views.admin_api_key_edit, name="admin-api-key-edit"),
    path("admin/requests/", views.admin_api_key_request_list, name="admin-api-key-request-list"),
    path("admin/requests/<int:request_id>/review/", views.admin_api_key_request_review, name="admin-api-key-request-review"),
]
