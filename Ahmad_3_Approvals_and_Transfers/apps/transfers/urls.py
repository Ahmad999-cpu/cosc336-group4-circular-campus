from django.urls import path

from . import views

app_name = "transfers"
urlpatterns = [
    path("", views.queue, name="queue"),
    path("<uuid:pk>/approve/", views.approve, name="approve"),
    path("<uuid:pk>/reject/", views.reject, name="reject"),
    path("transfers/", views.board, name="board"),
    path("transfers/<uuid:pk>/dispatch/", views.do_dispatch, name="dispatch"),
    path("transfers/<uuid:pk>/event/", views.delivery_event, name="event"),
    path("transfers/events/<uuid:event_pk>/resolve/", views.resolve, name="resolve"),
    path("receive/<uuid:pk>/", views.receive, name="receive"),
    path("cancel/<uuid:pk>/", views.cancel, name="cancel"),
]
