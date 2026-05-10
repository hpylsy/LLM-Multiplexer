from django.urls import path

from quota import views

urlpatterns = [
    path("my/", views.my_quota, name="my-quota"),
]
