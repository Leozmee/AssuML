"""Tests des vues Django — @admin_required et @login_required."""

import pytest


@pytest.mark.django_db
class TestAdminRequired:
    """Vérifie que les pages admin redirigent les non-admins."""

    def test_gestion_anonyme_redirige(self, client):
        resp = client.get("/gestion/")
        assert resp.status_code == 302
        assert "/accounts/login/" in resp["Location"]

    def test_gestion_user_redirige(self, user_client):
        resp = user_client.get("/gestion/")
        assert resp.status_code == 302
        assert "/accounts/login/" in resp["Location"]

    def test_scoring_anonyme_redirige(self, client):
        resp = client.get("/scoring/")
        assert resp.status_code == 302

    def test_analytics_anonyme_redirige(self, client):
        resp = client.get("/analytics/")
        assert resp.status_code == 302

    def test_monitoring_anonyme_redirige(self, client):
        resp = client.get("/monitoring/")
        assert resp.status_code == 302

    def test_actualites_anonyme_redirige(self, client):
        resp = client.get("/actualites/")
        assert resp.status_code == 302


@pytest.mark.django_db
class TestLoginRequired:
    def test_mon_compte_anonyme_redirige(self, client):
        resp = client.get("/accounts/mon-compte/")
        assert resp.status_code == 302
        assert "/accounts/login/" in resp["Location"]


@pytest.mark.django_db
class TestPagesPubliques:
    def test_login_page_ok(self, client):
        resp = client.get("/accounts/login/")
        assert resp.status_code == 200

    def test_register_page_ok(self, client):
        resp = client.get("/accounts/register/")
        assert resp.status_code == 200
