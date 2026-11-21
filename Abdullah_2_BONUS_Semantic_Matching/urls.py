from django.urls import path

from . import views

app_name = "matching"
urlpatterns = [
    path("", views.find, name="find"),
    path("before-buying/", views.procure, name="procure"),
    path("saved/", views.saved, name="saved"),
    path("interest/<uuid:pk>/", views.interest, name="interest"),
    path("saved/new/", views.need_form, name="need_new"),
    path("saved/<uuid:pk>/edit/", views.need_form, name="need_edit"),
    path("saved/<uuid:pk>/<str:action>/", views.need_action, name="need_action"),
    path("for/<uuid:pk>/", views.for_request, name="for_request"),
    path("<uuid:pk>/not-for-me/", views.not_for_me, name="not_for_me"),
    path("<uuid:pk>/choose/", views.choose, name="choose"),
]
