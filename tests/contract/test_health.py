"""
Tests contract pour l'endpoint /health — AssuML API.

Vérifie que le health check retourne le bon format et le bon statut.
Nécessite l'API en cours d'exécution sur le port 8000.
"""

import pytest
import httpx

BASE_URL = "http://localhost:8000"

pytestmark = pytest.mark.integration


def test_health_retourne_200():
    """GET /health doit retourner HTTP 200."""
    r = httpx.get(f"{BASE_URL}/health")
    assert r.status_code == 200


def test_health_format_json():
    """GET /health doit retourner un JSON avec les clés attendues."""
    r = httpx.get(f"{BASE_URL}/health")
    data = r.json()
    assert "status" in data
    assert "database" in data
    assert "models" in data


def test_health_status_ok():
    """GET /health doit retourner status='ok' quand tout fonctionne."""
    r = httpx.get(f"{BASE_URL}/health")
    data = r.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert data["models"] == "ok"
