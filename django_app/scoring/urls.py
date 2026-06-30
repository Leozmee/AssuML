"""URLs de l'application scoring."""

from django.urls import path

from scoring import views

app_name = "scoring"

urlpatterns = [
    path("", views.scoring_view, name="index"),
]
