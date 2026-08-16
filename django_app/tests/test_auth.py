"""Tests d'authentification — double rôle admin/user."""

from unittest.mock import patch

import pytest

from accounts.models import User


@pytest.mark.django_db
class TestLogin:
    def test_login_admin_redirige_gestion(self, client, admin_user):
        resp = client.post(
            "/accounts/login/",
            {
                "email": "admin_test@assuml.fr",
                "password": "pwd123",
            },
        )
        assert resp.status_code == 302
        assert "/gestion/" in resp["Location"]

    def test_login_user_redirige_mon_compte(self, client, client_user):
        resp = client.post(
            "/accounts/login/",
            {
                "email": "user_test@assuml.fr",
                "password": "pwd123",
            },
        )
        assert resp.status_code == 302
        assert "/mon-compte/" in resp["Location"]

    def test_login_mauvais_mot_de_passe(self, client, admin_user):
        resp = client.post(
            "/accounts/login/",
            {
                "email": "admin_test@assuml.fr",
                "password": "mauvais",
            },
        )
        assert resp.status_code == 200  # Reste sur la page de login


@pytest.mark.django_db
class TestRegisterRollback:
    """Vérifie le rollback si l'API FastAPI échoue à la création du client.

    L'inscription se fait en 2 étapes (étape 1 : email/mdp en session,
    étape 2 : profil → création atomique User + client FastAPI).
    """

    def _remplir_etape1(self, client, email):
        client.post(
            "/accounts/register/",
            {
                "email": email,
                "password1": "TestPass123!",
                "password2": "TestPass123!",
            },
        )

    @patch("accounts.views.api_client.create_client")
    def test_rollback_si_api_echoue(self, mock_create, client):
        from utils.api_client import ApiError

        mock_create.side_effect = ApiError(500, "Erreur serveur")

        self._remplir_etape1(client, "nouveau@test.fr")
        nb_users_avant = User.objects.count()
        resp = client.post(
            "/accounts/register/profil/",
            {
                "nom": "Dupont",
                "prenom": "Jean",
                "age": 30,
                "sexe": "homme",
                "poids": "75.0",
                "taille": "175",
                "enfants": 0,
                "fumeur": False,
                "region": "southwest",
            },
        )
        # Pas de redirection → reste sur le formulaire
        assert resp.status_code == 200
        # User rollbacké — le nombre de users n'augmente pas
        assert User.objects.count() == nb_users_avant

    @patch("accounts.views.api_client.create_client")
    def test_inscription_succes(self, mock_create, client):
        mock_create.return_value = {"client_id": 999}

        self._remplir_etape1(client, "nouveau2@test.fr")
        resp = client.post(
            "/accounts/register/profil/",
            {
                "nom": "Dupont",
                "prenom": "Jean",
                "age": 30,
                "sexe": "homme",
                "poids": "75.0",
                "taille": "175",
                "enfants": 0,
                "fumeur": False,
                "region": "southwest",
            },
        )
        assert resp.status_code == 302
        assert User.objects.filter(email="nouveau2@test.fr").exists()
        user = User.objects.get(email="nouveau2@test.fr")
        assert user.profil.role == "user"
        assert user.profil.client_id == 999


@pytest.mark.django_db
class TestCreateAdmin:
    """Création d'un compte admin — réservée au super-admin (is_superuser)."""

    def test_create_admin_accessible_superuser(self, superuser_client):
        resp = superuser_client.get("/accounts/create-admin/")
        assert resp.status_code == 200

    def test_create_admin_inaccessible_admin_classique(self, admin_client):
        resp = admin_client.get("/accounts/create-admin/")
        assert resp.status_code == 302

    def test_create_admin_inaccessible_user(self, user_client):
        resp = user_client.get("/accounts/create-admin/")
        assert resp.status_code == 302
