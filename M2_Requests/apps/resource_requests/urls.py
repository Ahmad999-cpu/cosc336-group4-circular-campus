from django.urls import path

from . import views

app_name = "resource_requests"
urlpatterns = [
    path("", views.mine, name="mine"),
    path("new/", views.new, name="new"),
    path("<uuid:pk>/", views.detail, name="detail"),
    path("<uuid:pk>/edit/", views.edit, name="edit"),
    path("<uuid:pk>/cancel/", views.cancel, name="cancel"),
]
