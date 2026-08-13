"""Tests d'accessibilité structurelle — WCAG 2.1 AA / RGAA 4.1 (feature 015).

Vérifie par analyse du HTML rendu (django.test.Client) la présence des
attributs/structure sémantiques attendus : lang, lien d'évitement, landmarks,
labels de formulaire, aria-label sur boutons icône, caption/th scope,
aria-live. Le contraste rendu, la navigation clavier réelle et le test au
lecteur d'écran ne sont pas vérifiables par ce fichier — cf. docs/accessibilite.md.
"""

import re

import pytest


@pytest.mark.django_db
class TestFocusOutline:
    """US1 — le focus clavier ne doit jamais être supprimé par du CSS."""

    def test_aucune_regle_outline_none_globale(self):
        with open("static/css/assuml.css", encoding="utf-8") as f:
            css = f.read()
        assert not re.search(r"outline\s*:\s*(none|0)\s*;", css), (
            "Une règle CSS supprime l'indicateur de focus clavier "
            "(outline: none/0) — interdit par WCAG 2.1 AA (2.4.7)."
        )


@pytest.mark.django_db
class TestStructureSemantique:
    """US2 — landmarks, lang, lien d'évitement."""

    def test_lang_fr_sur_html(self, client):
        resp = client.get("/accounts/login/")
        assert b'<html lang="fr"' in resp.content

    def test_lien_evitement_present(self, client):
        resp = client.get("/accounts/login/")
        assert b"Aller au contenu principal" in resp.content

    def test_landmarks_presents_page_connectee(self, admin_client):
        resp = admin_client.get("/gestion/")
        html = resp.content.decode()
        assert "<header" in html
        assert 'aria-label="Navigation principale"' in html
        assert 'id="main-content"' in html
        assert "<footer" in html


@pytest.mark.django_db
class TestFormulaires:
    """US3 — labels associés aux champs sur un échantillon représentatif."""

    def test_labels_associes_login(self, client):
        resp = client.get("/accounts/login/")
        html = resp.content.decode()
        assert 'for="id_email"' in html
        assert 'for="id_password"' in html

    def test_labels_associes_creation_client(self, admin_client):
        resp = admin_client.get("/gestion/create/")
        html = resp.content.decode()
        assert 'for="id_nom"' in html
        assert 'for="id_prenom"' in html
        assert 'for="id_age"' in html


@pytest.mark.django_db
class TestBoutonsIcones:
    """US4 — aria-label explicite sur les boutons d'action de la liste clients."""

    def test_aria_label_sur_actions_liste(self, admin_client):
        resp = admin_client.get("/gestion/")
        html = resp.content.decode()
        assert "aria-label=" in html


@pytest.mark.django_db
class TestTableaux:
    """US5 — caption et th scope sur le tableau clients."""

    def test_caption_et_scope_liste_clients(self, admin_client):
        resp = admin_client.get("/gestion/")
        html = resp.content.decode()
        assert "<caption" in html
        assert 'scope="col"' in html


@pytest.mark.django_db
class TestZonesDynamiques:
    """US7 — aria-live sur le monitoring."""

    def test_aria_live_monitoring(self, admin_client):
        resp = admin_client.get("/monitoring/")
        html = resp.content.decode()
        assert 'aria-live="polite"' in html
