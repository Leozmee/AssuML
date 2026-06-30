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
    """Vérifie le rollback si l'API FastAPI échoue à la création du client."""

    @patch("accounts.views.api_client.create_client")
    def test_rollback_si_api_echoue(self, mock_create, client):
        from utils.api_client import ApiError

        mock_create.side_effect = ApiError(500, "Erreur serveur")

        nb_users_avant = User.objects.count()
        resp = client.post(
            "/accounts/register/",
            {
                "email": "nouveau@test.fr",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
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
        mock_create.return_value = {"id": 999}

        resp = client.post(
            "/accounts/register/",
            {
                "email": "nouveau2@test.fr",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
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
    def test_create_admin_accessible_admin(self, admin_client):
        resp = admin_client.get("/accounts/create-admin/")
        assert resp.status_code == 200

    def test_create_admin_inaccessible_user(self, user_client):
        resp = user_client.get("/accounts/create-admin/")
        assert resp.status_code == 302
