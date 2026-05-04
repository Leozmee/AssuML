"""
Tests d'intégration — connexion PostgreSQL réelle.

Requiert un PostgreSQL actif avec la base assuml_db et l'utilisateur assuml_user.
Marqués @pytest.mark.integration pour être exclus du CI standard.

Exécution :
    pytest tests/integration/test_db_connection.py -v -m integration
"""

import pytest
from sqlalchemy import text

from database.connection import engine, SessionLocal
from database import crud


pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def db_session():
    """Session PostgreSQL réelle pour les tests d'intégration."""
    db = SessionLocal()
    yield db
    db.rollback()
    db.close()


def test_connexion_postgresql():
    """La connexion à PostgreSQL doit réussir."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_regions_preremplies(db_session):
    """La table regions doit contenir exactement 4 régions."""
    result = db_session.execute(text("SELECT COUNT(*) FROM regions"))
    count = result.scalar()
    assert count == 4, f"Attendu 4 régions, obtenu {count}"


def test_regions_valeurs(db_session):
    """Les 4 régions doivent correspondre aux valeurs attendues."""
    result = db_session.execute(
        text("SELECT nom_region FROM regions ORDER BY nom_region")
    )
    noms = [row[0] for row in result]
    assert set(noms) == {"southwest", "southeast", "northwest", "northeast"}


def test_create_et_read_client_postgresql(db_session):
    """Créer et relire un client sur PostgreSQL réel."""
    # Récupérer une region_id valide
    result = db_session.execute(
        text("SELECT region_id FROM regions WHERE nom_region = 'southwest'")
    )
    region_id = result.scalar()

    client = crud.create_client(
        db_session,
        age=30,
        sexe="homme",
        imc=23.5,
        enfants=1,
        fumeur=False,
        region_id=region_id,
    )
    assert client.client_id is not None

    # Relire depuis la base
    lu = crud.get_client(db_session, client.client_id)
    assert lu is not None
    assert lu.age == 30
    assert lu.sexe == "homme"

    # Nettoyage
    db_session.delete(lu)
    db_session.commit()


def test_soft_delete_postgresql(db_session):
    """Le soft delete ne doit pas supprimer physiquement la ligne."""
    result = db_session.execute(
        text("SELECT region_id FROM regions WHERE nom_region = 'northeast'")
    )
    region_id = result.scalar()

    client = crud.create_client(
        db_session,
        age=45,
        sexe="femme",
        imc=27.0,
        enfants=2,
        fumeur=True,
        region_id=region_id,
    )
    crud.soft_delete_client(db_session, client.client_id)

    # La ligne existe toujours
    result = db_session.execute(
        text("SELECT date_suppression FROM clients WHERE client_id = :id"),
        {"id": client.client_id},
    )
    row = result.fetchone()
    assert row is not None
    assert row[0] is not None  # date_suppression définie

    # N'apparaît plus dans get_clients actifs
    actifs = crud.get_clients(db_session, actifs_only=True)
    ids_actifs = [c.client_id for c in actifs]
    assert client.client_id not in ids_actifs

    # Nettoyage
    db_session.execute(
        text("DELETE FROM clients WHERE client_id = :id"),
        {"id": client.client_id},
    )
    db_session.commit()
