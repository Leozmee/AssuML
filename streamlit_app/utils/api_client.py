"""
Client HTTP centralisé pour appels vers FastAPI — AssuML Streamlit.

Toutes les fonctions retournent (data, error) :
  - data : objet Python si succès
  - error : message string si échec, None si succès
"""

import os
from pathlib import Path
from typing import Any, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

BASE_URL = "http://localhost:8000/api"
TIMEOUT = 10

# Clé API lue depuis .env — transmise dans le header X-API-Key sur chaque requête
_HEADERS = {"X-API-Key": os.getenv("API_KEY", "")}


def _get(endpoint: str, params: dict = None) -> Tuple[Any, Optional[str]]:
    try:
        r = requests.get(
            f"{BASE_URL}{endpoint}", params=params, headers=_HEADERS, timeout=TIMEOUT
        )
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "API indisponible — vérifiez que FastAPI tourne sur le port 8000."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erreur {e.response.status_code} : {detail}"
    except Exception as e:
        return None, str(e)


def _post(endpoint: str, data: dict) -> Tuple[Any, Optional[str]]:
    try:
        r = requests.post(
            f"{BASE_URL}{endpoint}", json=data, headers=_HEADERS, timeout=TIMEOUT
        )
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "API indisponible — vérifiez que FastAPI tourne sur le port 8000."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erreur {e.response.status_code} : {detail}"
    except Exception as e:
        return None, str(e)


def _put(endpoint: str, data: dict) -> Tuple[Any, Optional[str]]:
    try:
        r = requests.put(
            f"{BASE_URL}{endpoint}", json=data, headers=_HEADERS, timeout=TIMEOUT
        )
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "API indisponible — vérifiez que FastAPI tourne sur le port 8000."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erreur {e.response.status_code} : {detail}"
    except Exception as e:
        return None, str(e)


def _delete(endpoint: str) -> Tuple[Any, Optional[str]]:
    try:
        r = requests.delete(f"{BASE_URL}{endpoint}", headers=_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "API indisponible — vérifiez que FastAPI tourne sur le port 8000."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erreur {e.response.status_code} : {detail}"
    except Exception as e:
        return None, str(e)


# ── Health ─────────────────────────────────────────────────────────────────────


def get_health():
    return _get("/health")


# ── Stats ──────────────────────────────────────────────────────────────────────


def get_kpis():
    return _get("/stats/kpis")


# ── Clients ────────────────────────────────────────────────────────────────────


def get_clients(skip: int = 0, limit: int = 100):
    return _get("/clients/", params={"skip": skip, "limit": limit})


def get_all_clients():
    """Récupère tous les clients en gérant la pagination (limite API = 100)."""
    all_clients = []
    skip = 0
    limit = 100
    while True:
        data, err = get_clients(skip=skip, limit=limit)
        if err:
            return None, err
        if not data:
            break
        all_clients.extend(data)
        if len(data) < limit:
            break
        skip += limit
    return all_clients, None


def get_client(client_id: int):
    return _get(f"/clients/{client_id}")


def create_client(data: dict):
    return _post("/clients/", data)


def update_client(client_id: int, data: dict):
    return _put(f"/clients/{client_id}", data)


def delete_client(client_id: int):
    return _delete(f"/clients/{client_id}")


# ── Prédictions ML ─────────────────────────────────────────────────────────────


def predict_cout(data: dict):
    return _post("/predict/cout", data)


def predict_risque(data: dict):
    return _post("/predict/risque", data)


def predict_complet(data: dict):
    return _post("/predict/complet", data)


# ── Contrats ───────────────────────────────────────────────────────────────────


def get_contrats(client_id: int = None, skip: int = 0, limit: int = 100):
    params = {"skip": skip, "limit": limit}
    if client_id is not None:
        params["client_id"] = client_id
    return _get("/contrats/", params=params)


def get_all_contrats():
    """Récupère tous les contrats en gérant la pagination."""
    all_contrats = []
    skip = 0
    limit = 100
    while True:
        data, err = get_contrats(skip=skip, limit=limit)
        if err:
            return None, err
        if not data:
            break
        all_contrats.extend(data)
        if len(data) < limit:
            break
        skip += limit
    return all_contrats, None


def create_contrat(data: dict):
    return _post("/contrats/", data)


def update_contrat_statut(contrat_id: int, statut: str):
    return _put(f"/contrats/{contrat_id}/statut", {"statut": statut})


# ── Sinistres ──────────────────────────────────────────────────────────────────


def get_sinistres(contrat_id: int = None, skip: int = 0, limit: int = 100):
    params = {"skip": skip, "limit": limit}
    if contrat_id is not None:
        params["contrat_id"] = contrat_id
    return _get("/sinistres/", params=params)


def get_all_sinistres():
    """Récupère tous les sinistres en gérant la pagination."""
    all_sinistres = []
    skip = 0
    limit = 100
    while True:
        data, err = get_sinistres(skip=skip, limit=limit)
        if err:
            return None, err
        if not data:
            break
        all_sinistres.extend(data)
        if len(data) < limit:
            break
        skip += limit
    return all_sinistres, None


def create_sinistre(data: dict):
    return _post("/sinistres/", data)


def update_sinistre_statut(sinistre_id: int, statut: str):
    return _put(f"/sinistres/{sinistre_id}/statut", {"statut_sinistre": statut})


# ── Articles ───────────────────────────────────────────────────────────────────


def get_articles(source: str = None, skip: int = 0, limit: int = 100):
    params = {"skip": skip, "limit": limit}
    if source:
        params["source"] = source
    return _get("/articles/", params=params)


# ── Météo ──────────────────────────────────────────────────────────────────────


def get_meteo(region: str = None, saison: str = None, skip: int = 0, limit: int = 100):
    params = {"skip": skip, "limit": limit}
    if region:
        params["region"] = region
    if saison:
        params["saison"] = saison
    return _get("/meteo/", params=params)
