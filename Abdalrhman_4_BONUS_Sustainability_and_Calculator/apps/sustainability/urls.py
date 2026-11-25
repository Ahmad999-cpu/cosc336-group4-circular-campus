from django.urls import path

from . import views

app_name = "sustainability"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("calculator/", views.calculator_page, name="calculator"),
    path("compare/<uuid:pk>/", views.compare, name="compare"),
    path("actions/<uuid:pk>/", views.advice_panel, name="advice"),
    path("actions/<uuid:pk>/ai/", views.advice_ai, name="advice_ai"),
]
