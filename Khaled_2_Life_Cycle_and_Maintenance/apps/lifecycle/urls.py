from django.urls import path

from . import views

app_name = "lifecycle"
urlpatterns = [
    path("", views.board, name="maintenance"),
    path("asset/<uuid:pk>/", views.history, name="history"),
    path("asset/<uuid:pk>/report/", views.report, name="report"),
    path("asset/<uuid:pk>/end-of-life/", views.propose, name="propose"),
    path("events/<uuid:event_pk>/correct/", views.correct, name="correct"),
    path("records/<uuid:rec_pk>/start/", views.start, name="start"),
    path("records/<uuid:rec_pk>/repair/", views.repair, name="repair"),
    path("records/<uuid:rec_pk>/back/", views.back_in_service, name="back"),
    path("proposals/<uuid:p_pk>/decide/", views.decide, name="decide"),
    path("proposals/<uuid:p_pk>/complete/", views.complete, name="complete"),
]
