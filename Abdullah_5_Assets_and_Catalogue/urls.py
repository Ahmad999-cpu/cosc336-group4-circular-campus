from django.urls import path

from . import views

app_name = "catalogue"
urlpatterns = [
    path("", views.browse, name="browse"),
    path("ours/", views.mine, name="mine"),
    path("new/", views.new, name="new"),
    path("suggest/", views.suggest, name="suggest"),
    path("questions/", views.questions, name="questions"),
    path("import/", views.import_start, name="import"),
    path("import/template.csv", views.import_template, name="import_template"),
    path("import/<uuid:pk>/", views.import_batch, name="import_batch"),
    path("questions/<uuid:q_pk>/answer/", views.answer, name="answer"),
    path("questions/<uuid:q_pk>/withdraw/", views.withdraw, name="withdraw"),
    path("<uuid:pk>/ask/", views.ask, name="ask"),
    path("<uuid:pk>/", views.panel, name="panel"),
    path("<uuid:pk>/edit/", views.edit, name="edit"),
    path("<uuid:pk>/qr/", views.qr_label, name="qr"),
    path("<uuid:pk>/coming-soon/", views.upcoming_form, name="upcoming"),
    path("<uuid:pk>/coming-soon/cancel/", views.upcoming_cancel, name="upcoming_cancel"),
    path("<uuid:pk>/qr/label.svg", views.qr_download, name="qr_download"),
    path("<uuid:pk>/<str:action>/", views.act, name="act"),
]
