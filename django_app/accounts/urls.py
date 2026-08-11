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
    path("mon-compte/edit/", views.mon_compte_edit_view, name="mon_compte_edit"),
]
