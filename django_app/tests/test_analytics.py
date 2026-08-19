"""Tests pour le panneau Analytics — Contexte régional (feature 016).

api_client.get_meteo/get_stats_regionales sont mockés (monkeypatch) pour ne
pas dépendre d'un serveur FastAPI réellement démarré ; le Parquet Big Data
et DuckDB sont lus réellement (fichier local, rapide — même approche que
tests/unit/test_duckdb_analytics.py).
"""

import pytest

from analytics import views as analytics_views

METEO = [
    {
        "meteo_id": 1,
        "region_id": 1,
        "temperature_moy": 22.9,
        "humidite_moy": 41.0,
        "precipitations": 0.0,
        "saison": "ete",
    },
    {
        "meteo_id": 2,
        "region_id": 2,
        "temperature_moy": 20.3,
        "humidite_moy": 43.0,
        "precipitations": 0.0,
        "saison": "ete",
    },
    {
        "meteo_id": 3,
        "region_id": 3,
        "temperature_moy": 15.9,
        "humidite_moy": 74.0,
        "precipitations": 0.0,
        "saison": "ete",
    },
    {
        "meteo_id": 4,
        "region_id": 4,
        "temperature_moy": 19.1,
        "humidite_moy": 34.0,
        "precipitations": 0.0,
        "saison": "ete",
    },
]

STATS_REGIONALES = [
    {
        "stats_id": 1,
        "region_id": 1,
        "taux_obesite": 29.5,
        "taux_tabagisme": 14.0,
        "esperance_vie": 78.5,
        "taux_diabete": 10.5,
        "medecins_pour_100k": 255.0,
        "taux_non_assures": 15.5,
    },
    {
        "stats_id": 2,
        "region_id": 2,
        "taux_obesite": 35.8,
        "taux_tabagisme": 19.5,
        "esperance_vie": 75.9,
        "taux_diabete": 13.2,
        "medecins_pour_100k": 210.0,
        "taux_non_assures": 13.0,
    },
    {
        "stats_id": 3,
        "region_id": 3,
        "taux_obesite": 27.6,
        "taux_tabagisme": 15.0,
        "esperance_vie": 79.2,
        "taux_diabete": 9.0,
        "medecins_pour_100k": 270.0,
        "taux_non_assures": 11.0,
    },
    {
        "stats_id": 4,
        "region_id": 4,
        "taux_obesite": 26.9,
        "taux_tabagisme": 13.5,
        "esperance_vie": 80.1,
        "taux_diabete": 9.5,
        "medecins_pour_100k": 310.0,
        "taux_non_assures": 5.5,
    },
]


@pytest.mark.django_db
def test_contexte_regional_affiche_avec_sources_peuplees(admin_client, monkeypatch):
    """La section Contexte régional s'affiche avec météo + stats régionales."""
    monkeypatch.setattr(analytics_views.api_client, "get_meteo", lambda **kw: METEO)
    monkeypatch.setattr(
        analytics_views.api_client,
        "get_stats_regionales",
        lambda **kw: STATS_REGIONALES,
    )

    resp = admin_client.get("/analytics/")
    html = resp.content.decode()

    assert resp.status_code == 200
    assert "Contexte régional" in html
    assert 'th scope="col"' in html
    assert "Taux d&#x27;obésité" in html or "Taux d'obésité" in html


@pytest.mark.django_db
def test_contexte_regional_message_si_meteo_vide(admin_client, monkeypatch):
    """Page utilisable + message d'indisponibilité si la météo n'est pas chargée."""
    monkeypatch.setattr(analytics_views.api_client, "get_meteo", lambda **kw: [])
    monkeypatch.setattr(
        analytics_views.api_client,
        "get_stats_regionales",
        lambda **kw: STATS_REGIONALES,
    )

    resp = admin_client.get("/analytics/")
    html = resp.content.decode()

    assert resp.status_code == 200
    assert "Contexte régional indisponible" in html


@pytest.mark.django_db
def test_contexte_regional_message_si_stats_regionales_vide(admin_client, monkeypatch):
    """Page utilisable + message d'indisponibilité si stats régionales vides."""
    monkeypatch.setattr(analytics_views.api_client, "get_meteo", lambda **kw: METEO)
    monkeypatch.setattr(
        analytics_views.api_client, "get_stats_regionales", lambda **kw: []
    )

    resp = admin_client.get("/analytics/")
    html = resp.content.decode()

    assert resp.status_code == 200
    assert "Contexte régional indisponible" in html
