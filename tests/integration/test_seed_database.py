"""
Tests d'intégration pour database/seed.py.

Vérifie que le seed peuple correctement la BDD et est idempotent.
Nécessite PostgreSQL en cours d'exécution avec les variables d'env configurées.
"""

import pytest

from database.connection import SessionLocal
from database.models import Client, Contrat, Prediction, Region, Sinistre
from database.seed import main as seed_main


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def session():
    """Ouvre une session SQLAlchemy pour les tests d'intégration."""
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module", autouse=True)
def run_seed():
    """Lance le seed une fois avant tous les tests du module."""
    seed_main()


# ── Tests peuplement ──────────────────────────────────────────────────────────


def test_regions_count(session):
    """La table regions doit contenir exactement 4 lignes après seed."""
    count = session.query(Region).count()
    assert count == 4, f"Attendu 4 régions, obtenu {count}"


def test_clients_count(session):
    """La table clients doit contenir exactement 1 338 lignes après seed."""
    count = session.query(Client).count()
    assert count == 1338, f"Attendu 1 338 clients, obtenu {count}"


def test_seed_idempotent(session):
    """Relancer le seed ne doit pas créer de doublons."""
    seed_main()
    count = session.query(Client).count()
    assert count == 1338, f"Doublon détecté : {count} clients au lieu de 1 338"


# ── Tests valeurs métier ──────────────────────────────────────────────────────


def test_sexe_valeurs_valides(session):
    """Tous les clients doivent avoir sexe dans {homme, femme}."""
    valeurs = {row[0] for row in session.query(Client.sexe).distinct()}
    assert valeurs.issubset({"homme", "femme"}), f"Valeurs inattendues : {valeurs}"


def test_fumeur_booleen(session):
    """fumeur doit être un booléen True ou False pour tous les clients."""
    valeurs = {row[0] for row in session.query(Client.fumeur).distinct()}
    assert valeurs.issubset({True, False}), f"Valeurs inattendues : {valeurs}"


def test_region_id_valides(session):
    """Tous les clients doivent avoir un region_id référençant une région existante."""
    regions_ids = {row[0] for row in session.query(Region.region_id)}
    clients_region_ids = {row[0] for row in session.query(Client.region_id).distinct()}
    assert clients_region_ids.issubset(
        regions_ids
    ), f"region_id orphelins : {clients_region_ids - regions_ids}"


# ── Tests tables vides (US3) ──────────────────────────────────────────────────


def test_predictions_vide(session):
    """La table predictions doit être vide après seed."""
    count = session.query(Prediction).count()
    assert count == 0, f"predictions non vide : {count} ligne(s)"


def test_contrats_vide(session):
    """La table contrats doit être vide après seed."""
    count = session.query(Contrat).count()
    assert count == 0, f"contrats non vide : {count} ligne(s)"


def test_sinistres_vide(session):
    """La table sinistres doit être vide après seed."""
    count = session.query(Sinistre).count()
    assert count == 0, f"sinistres non vide : {count} ligne(s)"
