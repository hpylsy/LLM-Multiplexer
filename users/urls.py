from django.urls import path

from users import views

urlpatterns = [
    path("profile/", views.profile_detail, name="profile"),
    path("admin/list/", views.admin_user_list, name="admin-user-list"),
    path("admin/create/", views.admin_user_create, name="admin-user-create"),
    path("admin/<int:user_id>/edit/", views.admin_user_edit, name="admin-user-edit"),
    path("admin/<int:user_id>/toggle/", views.admin_user_toggle, name="admin-user-toggle"),
    path("admin/<int:user_id>/delete/", views.admin_user_delete, name="admin-user-delete"),
    path("admin/batch/", views.admin_user_batch, name="admin-user-batch"),
]
