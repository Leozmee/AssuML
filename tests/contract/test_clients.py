"""
Tests contract pour les endpoints /api/clients — AssuML API.

Vérifie les comportements CRUD et la règle soft delete.
Nécessite l'API en cours d'exécution sur le port 8000.
"""

import os

import httpx
import pytest
from sqlalchemy import text

from database.connection import SessionLocal

BASE_URL = "http://localhost:8000"

# Le router clients est protégé par X-API-Key (cf. api/main.py) — la clé
# attendue est lue depuis la même variable d'environnement que l'API.
HEADERS = {"X-API-Key": os.getenv("API_KEY", "")}

pytestmark = pytest.mark.integration


def test_lister_clients_retourne_liste():
    """GET /api/clients/ doit retourner une liste non vide."""
    r = httpx.get(f"{BASE_URL}/api/clients/", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_lister_clients_format():
    """Chaque client doit avoir les champs attendus."""
    r = httpx.get(f"{BASE_URL}/api/clients/?limit=1", headers=HEADERS)
    data = r.json()
    client = data[0]
    assert "client_id" in client
    assert "age" in client
    assert "sexe" in client
    assert "imc" in client
    assert "fumeur" in client
    assert "date_suppression" in client


def test_obtenir_client_existant():
    """GET /api/clients/1 doit retourner le client avec client_id=1."""
    r = httpx.get(f"{BASE_URL}/api/clients/1", headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["client_id"] == 1


def test_obtenir_client_inexistant():
    """GET /api/clients/999999 doit retourner 404."""
    r = httpx.get(f"{BASE_URL}/api/clients/999999", headers=HEADERS)
    assert r.status_code == 404


def test_creer_et_supprimer_client():
    """POST crée un client, DELETE le désactive, GET confirme l'absence."""
    payload = {
        "age": 30,
        "sexe": "homme",
        "imc": 22.5,
        "enfants": 0,
        "fumeur": False,
        "region_id": 1,
    }
    r_create = httpx.post(f"{BASE_URL}/api/clients/", json=payload, headers=HEADERS)
    assert r_create.status_code == 201
    client_id = r_create.json()["client_id"]

    # Soft delete
    r_delete = httpx.delete(f"{BASE_URL}/api/clients/{client_id}", headers=HEADERS)
    assert r_delete.status_code == 200
    assert r_delete.json()["client_id"] == client_id

    # Le client ne doit plus apparaître dans la liste active
    r_get = httpx.get(f"{BASE_URL}/api/clients/{client_id}", headers=HEADERS)
    assert r_get.status_code == 404

    # Nettoyage : le soft delete de l'API laisse la ligne en base (comportement
    # attendu en production) — on la retire physiquement ici pour ne pas fausser
    # le COUNT(*) des tests de seed qui s'exécutent après celui-ci.
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM clients WHERE client_id = :id"), {"id": client_id})
        db.commit()
    finally:
        db.close()
