"""URLs de l'application actualites."""

from django.urls import path

from actualites import views

app_name = "actualites"

urlpatterns = [
    path("", views.actualites_list, name="list"),
]
