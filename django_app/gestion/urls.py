"""URLs de l'application gestion (admin uniquement)."""

from django.urls import path

from gestion import views

app_name = "gestion"

urlpatterns = [
    path("", views.client_list, name="list"),
    path("<int:client_id>/", views.client_detail, name="detail"),
    path("create/", views.client_create, name="create"),
    path("<int:client_id>/edit/", views.client_update, name="edit"),
    path("<int:client_id>/delete/", views.client_delete, name="delete"),
    path("<int:client_id>/scorer/", views.client_score, name="score"),
    path("<int:client_id>/contrat/", views.contrat_create, name="contrat_create"),
    path(
        "<int:client_id>/contrat/<int:contrat_id>/edit/",
        views.contrat_update_type,
        name="contrat_edit",
    ),
    path(
        "contrat/<int:contrat_id>/statut/",
        views.contrat_update_statut,
        name="contrat_statut",
    ),
    path(
        "contrat/<int:contrat_id>/prime/",
        views.contrat_update_prime,
        name="contrat_prime",
    ),
]
