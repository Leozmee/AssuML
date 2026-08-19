"""Client HTTP centralisé — Django vers FastAPI.

Toutes les méthodes lèvent une exception en cas d'erreur (jamais de tuple).
Les vues appellent ces méthodes dans un try/except et affichent
le message via Django messages framework.
"""

import requests
from django.conf import settings


class ApiUnavailableError(Exception):
    """FastAPI est inaccessible (ConnectionError)."""


class ApiTimeoutError(Exception):
    """La requête vers FastAPI a expiré."""


class ApiError(Exception):
    """Réponse HTTP 4xx/5xx de FastAPI."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Erreur {status_code} : {detail}")


def _headers() -> dict:
    """Headers HTTP avec clé API pour chaque requête."""
    return {"X-API-Key": settings.API_KEY}


def _base_url() -> str:
    return settings.API_BASE_URL.rstrip("/") + "/api"


def _handle_response(r: requests.Response):
    """Lève ApiError si la réponse HTTP est une erreur."""
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise ApiError(r.status_code, detail)
    return r.json()


def _get(endpoint: str, params: dict = None):
    try:
        r = requests.get(
            f"{_base_url()}{endpoint}",
            params=params,
            headers=_headers(),
            timeout=10,
        )
        return _handle_response(r)
    except requests.exceptions.ConnectionError as e:
        raise ApiUnavailableError(
            "API indisponible — vérifiez que FastAPI tourne sur le port 8000."
        ) from e
    except requests.exceptions.Timeout as e:
        raise ApiTimeoutError("La requête vers FastAPI a expiré (timeout 10s).") from e


def _post(endpoint: str, data: dict):
    try:
        r = requests.post(
            f"{_base_url()}{endpoint}",
            json=data,
            headers=_headers(),
            timeout=10,
        )
        return _handle_response(r)
    except requests.exceptions.ConnectionError as e:
        raise ApiUnavailableError(
            "API indisponible — vérifiez que FastAPI tourne sur le port 8000."
        ) from e
    except requests.exceptions.Timeout as e:
        raise ApiTimeoutError("La requête vers FastAPI a expiré (timeout 10s).") from e


def _put(endpoint: str, data: dict):
    try:
        r = requests.put(
            f"{_base_url()}{endpoint}",
            json=data,
            headers=_headers(),
            timeout=10,
        )
        return _handle_response(r)
    except requests.exceptions.ConnectionError as e:
        raise ApiUnavailableError(
            "API indisponible — vérifiez que FastAPI tourne sur le port 8000."
        ) from e
    except requests.exceptions.Timeout as e:
        raise ApiTimeoutError("La requête vers FastAPI a expiré (timeout 10s).") from e


def _delete(endpoint: str):
    try:
        r = requests.delete(
            f"{_base_url()}{endpoint}",
            headers=_headers(),
            timeout=10,
        )
        return _handle_response(r)
    except requests.exceptions.ConnectionError as e:
        raise ApiUnavailableError(
            "API indisponible — vérifiez que FastAPI tourne sur le port 8000."
        ) from e
    except requests.exceptions.Timeout as e:
        raise ApiTimeoutError("La requête vers FastAPI a expiré (timeout 10s).") from e


# ── Health ─────────────────────────────────────────────────────────────────────


def get_health():
    """GET /health — hors préfixe /api (convention infra standard : health
    check à la racine, cf. api/main.py), contrairement à tous les autres
    endpoints. On ne peut donc pas passer par `_get()`/`_base_url()`."""
    try:
        r = requests.get(
            f"{settings.API_BASE_URL.rstrip('/')}/health",
            headers=_headers(),
            timeout=10,
        )
        return _handle_response(r)
    except requests.exceptions.ConnectionError as e:
        raise ApiUnavailableError(
            "API indisponible — vérifiez que FastAPI tourne sur le port 8000."
        ) from e
    except requests.exceptions.Timeout as e:
        raise ApiTimeoutError("La requête vers FastAPI a expiré (timeout 10s).") from e


# ── Stats ──────────────────────────────────────────────────────────────────────


def get_stats_kpis():
    return _get("/stats/kpis")


def get_dernieres_predictions():
    return _get("/stats/dernieres-predictions")


def get_predictions_client(client_id: int):
    return _get(f"/predict/client/{client_id}")


# ── Clients ────────────────────────────────────────────────────────────────────


def get_clients(skip: int = 0, limit: int = 100, actifs_only: bool = True):
    return _get(
        "/clients/",
        params={"skip": skip, "limit": limit, "actifs_only": actifs_only},
    )


def get_all_clients(actifs_only: bool = True):
    """Récupère tous les clients en gérant la pagination (limite API = 100).

    actifs_only=False inclut aussi les clients désactivés (soft delete) —
    utilisé par la purge RGPD différée (cf. gestion/management/commands/
    purge_clients.py).
    """
    all_clients = []
    skip = 0
    limit = 100
    while True:
        data = get_clients(skip=skip, limit=limit, actifs_only=actifs_only)
        if not data:
            break
        all_clients.extend(data)
        if len(data) < limit:
            break
        skip += limit
    return all_clients


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
        data = get_contrats(skip=skip, limit=limit)
        if not data:
            break
        all_contrats.extend(data)
        if len(data) < limit:
            break
        skip += limit
    return all_contrats


def create_contrat(data: dict):
    return _post("/contrats/", data)


def update_contrat(contrat_id: int, data: dict):
    return _put(f"/contrats/{contrat_id}", data)


def update_contrat_statut(contrat_id: int, statut: str):
    return _put(f"/contrats/{contrat_id}/statut", {"statut": statut})


def update_contrat_prime(contrat_id: int, prime_mensuelle: float):
    return _put(f"/contrats/{contrat_id}/prime", {"prime_mensuelle": prime_mensuelle})


def update_contrat_type(contrat_id: int, type_couverture: str):
    return _put(f"/contrats/{contrat_id}/type", {"type_couverture": type_couverture})


# ── Articles ───────────────────────────────────────────────────────────────────


def get_articles(source: str = None, skip: int = 0, limit: int = 100):
    params = {"skip": skip, "limit": limit}
    if source:
        params["source"] = source
    return _get("/articles/", params=params)


# ── Météo ──────────────────────────────────────────────────────────────────────


def get_meteo(
    region: str = None,
    saison: str = None,
    skip: int = 0,
    limit: int = 100,
    dernier_par_region: bool = False,
):
    params = {"skip": skip, "limit": limit}
    if region:
        params["region"] = region
    if saison:
        params["saison"] = saison
    if dernier_par_region:
        params["dernier_par_region"] = "true"
    return _get("/meteo/", params=params)


# ── Statistiques régionales ──────────────────────────────────────────────────


def get_stats_regionales(region: str = None, skip: int = 0, limit: int = 100):
    params = {"skip": skip, "limit": limit}
    if region:
        params["region"] = region
    return _get("/stats-regionales/", params=params)
