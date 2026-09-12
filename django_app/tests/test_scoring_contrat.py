"""Tests des actions contrat proposées sous un résultat de Simulation ML.

La simulation ne propose d'ouvrir un contrat ou d'aligner la prime que
lorsqu'elle est rattachée à un client existant — c'est le seul cas où elle
est enregistrée dans son historique de prédictions. Une simulation libre ne
se rattache à aucun dossier : aucune action ne doit alors apparaître.

api_client et predict_complet sont mockés : ces tests portent sur la vue et
le gabarit, pas sur un serveur FastAPI démarré.
"""

import pytest

from scoring import views as scoring_views

CLIENT = {
    "client_id": 7,
    "nom": "Dupont",
    "prenom": "Jean",
    "age": 40,
    "sexe": "homme",
    "imc": 28.5,
    "enfants": 2,
    "fumeur": False,
    "region_id": 1,
    "a_un_compte": False,
}

CONTRAT = {
    "contrat_id": 3,
    "client_id": 7,
    "type_couverture": "standard",
    "prime_mensuelle": 990.0,
    "statut": "actif",
}

PREDICTION_BRUTE = {
    "cout_predit": 12000.0,
    "score_risque": 0.62,
    "categorie_risque": "moyen",
    "prime": 16200.0,
    "decision": "accepter",
    "prediction_id": 99,
}

FORMULAIRE = {
    "age": 40,
    "sexe": "homme",
    "poids": 85.0,
    "taille": 173.0,
    "enfants": 2,
    "fumeur": "",
    "region": "southwest",
}


@pytest.fixture
def api_mocke(monkeypatch):
    """Neutralise les appels FastAPI de la vue scoring.

    Retourne une fonction permettant de choisir si le client a un contrat.
    """

    def configurer(contrats):
        monkeypatch.setattr(
            scoring_views.api_client, "get_all_clients", lambda **kw: [CLIENT]
        )
        monkeypatch.setattr(
            scoring_views.api_client, "get_all_contrats", lambda **kw: contrats
        )
        monkeypatch.setattr(
            scoring_views.api_client, "get_dernieres_predictions", lambda **kw: []
        )
        monkeypatch.setattr(
            scoring_views, "predict_complet", lambda payload: dict(PREDICTION_BRUTE)
        )

    return configurer


@pytest.mark.django_db
def test_client_sans_contrat_propose_d_en_ouvrir(admin_client, api_mocke):
    """Un client sans contrat se voit proposer d'en ouvrir un."""
    api_mocke(contrats=[])
    resp = admin_client.post("/scoring/", {**FORMULAIRE, "client_id": "7"})
    html = resp.content.decode()

    assert resp.status_code == 200
    assert "Suite à donner" in html
    assert "Ouvrir un contrat" in html
    assert "Mettre à jour la prime" not in html
    # Le lien porte l'origine, pour revenir à la simulation après création
    assert "/gestion/7/contrat/?origine=scoring" in html


@pytest.mark.django_db
def test_client_avec_contrat_propose_la_mise_a_jour(admin_client, api_mocke):
    """Un client déjà sous contrat se voit proposer d'aligner sa prime."""
    api_mocke(contrats=[CONTRAT])
    resp = admin_client.post("/scoring/", {**FORMULAIRE, "client_id": "7"})
    html = resp.content.decode()

    assert resp.status_code == 200
    assert "Mettre à jour la prime" in html
    assert "Ouvrir un contrat" not in html
    assert "/gestion/contrat/3/prime/" in html
    assert 'name="origine" value="scoring"' in html


@pytest.mark.django_db
def test_simulation_libre_ne_propose_aucune_action(admin_client, api_mocke):
    """Sans client sélectionné, la simulation n'est rattachée à aucun dossier."""
    api_mocke(contrats=[CONTRAT])
    resp = admin_client.post("/scoring/", FORMULAIRE)
    html = resp.content.decode()

    assert resp.status_code == 200
    assert ">Suite à donner<" not in html
    assert "Ouvrir un contrat" not in html
    assert "Mettre à jour la prime" not in html
