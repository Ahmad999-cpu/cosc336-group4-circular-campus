from django.urls import path

from . import views

app_name = "reporting"
urlpatterns = [
    path("", views.index, name="index"),
    path("csv/", views.csv_export, name="csv"),
    path("demand/", views.demand, name="demand"),
    path("summary/", views.summarize, name="summarize"),
    path("summary/<uuid:pk>/publish/", views.publish, name="publish"),
    path("summary/<uuid:pk>/discard/", views.discard, name="discard"),
]
