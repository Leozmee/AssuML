"""Tests du client de métriques Railway et de son intégration au Monitoring.

L'exigence centrale testée ici est la dégradation : le panneau Monitoring est
la page de démonstration, elle doit rester affichable quoi qu'il arrive du côté
de Railway — jeton absent, service injoignable, réponse vide ou malformée.

Aucun appel réseau n'est effectué : requests.post est systématiquement mocké.
"""

import json

import pytest
import requests

from monitoring import railway

CONFIG = {
    "RAILWAY_API_TOKEN": "jeton-de-test",
    "RAILWAY_MONITORED_SERVICE_ID": "svc-123",
    "RAILWAY_MONITORED_ENVIRONMENT_ID": "env-456",
}


@pytest.fixture
def configure(monkeypatch):
    """Renseigne les trois variables d'environnement attendues."""
    for cle, valeur in CONFIG.items():
        monkeypatch.setenv(cle, valeur)


@pytest.fixture
def sans_config(monkeypatch):
    """Retire toute configuration Railway."""
    for cle in CONFIG:
        monkeypatch.delenv(cle, raising=False)


def _reponse(payload):
    """Fabrique un faux objet réponse requests exposant .json()."""

    class Fausse:
        def json(self):
            return payload

    return Fausse()


def _mock_post(monkeypatch, payload=None, exception=None):
    """Remplace requests.post par un double renvoyant payload, ou levant."""

    def faux_post(*args, **kwargs):
        if exception:
            raise exception
        return _reponse(payload)

    monkeypatch.setattr(railway.requests, "post", faux_post)


# ── Configuration ─────────────────────────────────────────────────────────────


def test_non_configure_si_variables_absentes(sans_config):
    assert railway.est_configure() is False


def test_configure_si_les_trois_variables_sont_presentes(configure):
    assert railway.est_configure() is True


def test_configuration_partielle_compte_comme_absente(configure, monkeypatch):
    """Deux variables sur trois ne suffisent pas — pas de requête bancale."""
    monkeypatch.delenv("RAILWAY_MONITORED_SERVICE_ID")
    assert railway.est_configure() is False


# ── Répartition entre les deux services observés ──────────────────────────────


def _capturer_services(monkeypatch):
    """Enregistre le serviceId envoyé à chaque requête GraphQL."""
    vus = []

    def faux_post(*args, **kwargs):
        vus.append(kwargs["json"]["variables"]["s"])

        class Fausse:
            def json(self):
                return {"data": {}}

        return Fausse()

    monkeypatch.setattr(railway.requests, "post", faux_post)
    return vus


def test_les_metriques_http_visent_le_service_web(configure, monkeypatch):
    """Railway ne compte le trafic qu'au proxy public : c'est le service web
    qui le reçoit, pas l'API appelée par le réseau privé."""
    monkeypatch.setenv("RAILWAY_MONITORED_WEB_SERVICE_ID", "svc-web")
    vus = _capturer_services(monkeypatch)
    railway.latence()
    railway.requetes()
    railway.codes_statut()
    assert set(vus) == {"svc-web"}


def test_la_memoire_vise_le_conteneur_declare(configure, monkeypatch):
    """La mémoire reste celle du conteneur qui sert les modèles."""
    monkeypatch.setenv("RAILWAY_MONITORED_WEB_SERVICE_ID", "svc-web")
    vus = _capturer_services(monkeypatch)
    railway.memoire()
    assert vus == [CONFIG["RAILWAY_MONITORED_SERVICE_ID"]]


def test_sans_service_web_un_seul_service_est_observe(configure, monkeypatch):
    """Configuration antérieure : le service déclaré sert aux deux usages."""
    monkeypatch.delenv("RAILWAY_MONITORED_WEB_SERVICE_ID", raising=False)
    vus = _capturer_services(monkeypatch)
    railway.latence()
    railway.memoire()
    assert set(vus) == {CONFIG["RAILWAY_MONITORED_SERVICE_ID"]}


# ── Dégradation ───────────────────────────────────────────────────────────────


def test_sans_configuration_les_graphiques_sont_vides(sans_config):
    resultat = railway.graphiques()
    assert resultat["configure"] is False
    assert resultat["disponible"] is False
    assert resultat["charts"] == {}


def test_railway_injoignable_ne_leve_pas(configure, monkeypatch):
    """Une panne réseau donne des graphiques vides, jamais une exception."""
    _mock_post(monkeypatch, exception=requests.ConnectionError("boom"))
    resultat = railway.graphiques()
    assert resultat["configure"] is True
    assert resultat["disponible"] is False


def test_timeout_ne_leve_pas(configure, monkeypatch):
    _mock_post(monkeypatch, exception=requests.Timeout("trop lent"))
    assert railway.graphiques()["disponible"] is False


def test_erreurs_graphql_ne_levent_pas(configure, monkeypatch):
    """Un jeton invalide renvoie des `errors` : traité comme une absence."""
    _mock_post(monkeypatch, payload={"errors": [{"message": "Not Authorized"}]})
    assert railway.graphiques()["disponible"] is False


def test_reponse_malformee_ne_leve_pas(configure, monkeypatch):
    """Un changement de forme côté Railway ne doit pas casser la page."""
    _mock_post(monkeypatch, payload={"data": {"httpMetrics": None}})
    assert railway.graphiques()["disponible"] is False


def test_json_invalide_ne_leve_pas(configure, monkeypatch):
    _mock_post(monkeypatch, exception=ValueError("pas du JSON"))
    assert railway.graphiques()["disponible"] is False


# ── Transformation des données ────────────────────────────────────────────────


def test_latence_produit_trois_traces_en_millisecondes(configure, monkeypatch):
    """Railway renvoie déjà des millisecondes : aucune conversion appliquée."""
    _mock_post(
        monkeypatch,
        payload={
            "data": {
                "httpDurationMetrics": {
                    "samples": [{"ts": 1789200000, "p50": 34, "p95": 36, "p99": 120}]
                }
            }
        },
    )
    traces = railway.latence()
    # Les libellés nomment ce que chaque percentile signifie, le code seul
    # ne parlant qu'aux initiés.
    assert [t["name"] for t in traces] == [
        "Médiane (p50)",
        "p95 — 5 % plus lentes",
        "p99 — 1 % plus lentes",
    ]
    assert [t["y"][0] for t in traces] == [34, 36, 120]


def test_requetes_produit_une_trace_en_barres(configure, monkeypatch):
    _mock_post(
        monkeypatch,
        payload={
            "data": {"httpMetrics": {"samples": [{"ts": 1789200000, "value": 42}]}}
        },
    )
    traces = railway.requetes()
    assert len(traces) == 1
    assert traces[0]["type"] == "bar"
    assert traces[0]["y"] == [42]


def test_codes_statut_regroupes_par_famille(configure, monkeypatch):
    """200 et 201 fusionnent en 2xx ; 500 reste distinct en 5xx."""
    _mock_post(
        monkeypatch,
        payload={
            "data": {
                "httpMetricsGroupedByStatus": [
                    {"statusCode": 200, "samples": [{"ts": 1789200000, "value": 10}]},
                    {"statusCode": 201, "samples": [{"ts": 1789200000, "value": 5}]},
                    {"statusCode": 500, "samples": [{"ts": 1789200000, "value": 3}]},
                ]
            }
        },
    )
    traces = {t["name"]: t["y"][0] for t in railway.codes_statut()}
    assert traces == {"2xx — Succès": 15, "5xx — Erreur du serveur": 3}


def test_memoire_convertit_en_megaoctets_et_trace_la_limite(configure, monkeypatch):
    """Railway renvoie des gigaoctets ; la limite est tracée en pointillés."""
    _mock_post(
        monkeypatch,
        payload={
            "data": {
                "metrics": [
                    {
                        "measurement": "MEMORY_USAGE_GB",
                        "values": [{"ts": 1789200000, "value": 0.5}],
                    },
                    {
                        "measurement": "MEMORY_LIMIT_GB",
                        "values": [{"ts": 1789200000, "value": 1.0}],
                    },
                ]
            }
        },
    )
    traces = railway.memoire()
    assert [t["y"][0] for t in traces] == [512.0, 1024.0]
    limite = next(t for t in traces if t["name"] == "Limite allouée")
    assert limite["line"]["dash"] == "dash"


def test_limite_memoire_nulle_devient_une_interruption(configure, monkeypatch):
    """Une limite à zéro est une absence de relevé, pas une limite de zéro."""
    _mock_post(
        monkeypatch,
        payload={
            "data": {
                "metrics": [
                    {
                        "measurement": "MEMORY_LIMIT_GB",
                        "values": [
                            {"ts": 1789200000, "value": 0},
                            {"ts": 1789200060, "value": 1.0},
                        ],
                    }
                ]
            }
        },
    )
    limite = railway.memoire()[0]
    assert limite["y"] == [None, 1024.0]


def test_graphiques_serialise_en_json(configure, monkeypatch):
    """Le composant Plotly attend du JSON, pas des objets Python."""
    _mock_post(
        monkeypatch,
        payload={
            "data": {"httpMetrics": {"samples": [{"ts": 1789200000, "value": 7}]}}
        },
    )
    resultat = railway.graphiques()
    assert isinstance(resultat["charts"]["requetes"], str)
    assert json.loads(resultat["charts"]["requetes"])[0]["y"] == [7]


# ── Intégration à la page ─────────────────────────────────────────────────────


@pytest.mark.django_db
def test_page_monitoring_s_affiche_sans_configuration(admin_client, sans_config):
    """Sans jeton, la page reste complète et explique ce qui manque."""
    resp = admin_client.get("/monitoring/")
    html = resp.content.decode()
    assert resp.status_code == 200
    assert "Monitoring système" in html
    assert "RAILWAY_API_TOKEN" in html


@pytest.mark.django_db
def test_page_monitoring_s_affiche_si_railway_tombe(
    admin_client, configure, monkeypatch
):
    """Railway injoignable : la page s'affiche, les KPIs restent là."""
    _mock_post(monkeypatch, exception=requests.ConnectionError("boom"))
    resp = admin_client.get("/monitoring/")
    html = resp.content.decode()
    assert resp.status_code == 200
    assert "Monitoring système" in html
    assert "momentanément indisponibles" in html
