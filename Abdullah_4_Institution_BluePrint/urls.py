from django.urls import path

from . import views

app_name = "blueprint"
urlpatterns = [
    path("", views.index, name="index"),
    path("units/new/", views.unit_form, name="unit_new"),
    path("units/<uuid:pk>/", views.unit_form, name="unit_edit"),
    path("units/<uuid:pk>/status/", views.unit_status, name="unit_status"),
    path("roles/new/", views.role_form, name="role_new"),
    path("roles/<uuid:pk>/", views.role_form, name="role_edit"),
    path("routes/new/", views.rule_form, name="rule_new"),
    path("routes/<uuid:pk>/", views.rule_form, name="rule_edit"),
    path("routes/<uuid:pk>/toggle/", views.rule_toggle, name="rule_toggle"),
    path("routes/try/", views.try_route, name="try"),
    path("start/template/<slug:key>/", views.from_template, name="from_template"),
    path("start/describe/", views.from_description, name="from_description"),
    path("drafts/<uuid:pk>/", views.draft, name="draft"),
    path("drafts/<uuid:pk>/publish/", views.publish, name="publish"),
    path("drafts/<uuid:pk>/discard/", views.discard, name="discard"),
]
