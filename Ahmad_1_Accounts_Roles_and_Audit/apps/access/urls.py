from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "access"
urlpatterns = [
    path("login/", views.SignInView.as_view(), name="login"),
    path("login/demo/", views.demo_sign_in, name="demo_login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password/", views.password_change, name="password"),
    path("people/", views.people, name="people"),
    path("people/new/", views.person_new, name="person_new"),
    path("people/<uuid:pk>/", views.person, name="person"),
    path("people/<uuid:pk>/status/", views.person_status, name="person_status"),
    path("people/<uuid:pk>/roles/", views.role_assign, name="role_assign"),
    path("people/<uuid:pk>/roles/<uuid:assignment_pk>/remove/", views.role_revoke, name="role_revoke"),
]
