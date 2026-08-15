"""URLs de l'application accounts."""

from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_step1_view, name="register"),
    path("register/profil/", views.register_step2_view, name="register_step2"),
    path("create-admin/", views.create_admin_view, name="create_admin"),
    path("mon-compte/", views.mon_compte_view, name="mon_compte"),
    path("mon-compte/export/", views.export_donnees_view, name="export_donnees"),
    path(
        "mon-compte/contrat/<int:contrat_id>/resilier/",
        views.resilier_contrat_view,
        name="resilier_contrat",
    ),
    path("mon-compte/simulation/", views.simulation_view, name="simulation"),
    path("mon-compte/edit/", views.mon_compte_edit_view, name="mon_compte_edit"),
]
