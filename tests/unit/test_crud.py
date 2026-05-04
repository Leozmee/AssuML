"""
Tests unitaires pour database/crud.py — utilise SQLite in-memory.

Aucune dépendance PostgreSQL requise : les tests tournent en CI
sans base de données réelle.
SQLite est utilisé uniquement pour tester la logique des fonctions CRUD,
pas les contraintes CHECK spécifiques à PostgreSQL.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database.models import Base, Client, Contrat, Prediction, Region, Sinistre
from database import crud

# ── Fixtures ──────────────────────────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def engine():
    """Engine SQLite in-memory pour les tests unitaires."""
    eng = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

    # SQLite ne supporte pas les FK par défaut — activation explicite
    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def db(engine):
    """Session SQLite pour chaque test — rollback automatique après le test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    # Pré-peupler la région de référence
    if session.query(Region).count() == 0:
        session.add(Region(nom_region="southwest"))
        session.commit()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def region_id(db):
    """Retourne l'ID de la région de test."""
    return db.query(Region).first().region_id


# ── Tests create_client ────────────────────────────────────────────────────────


def test_create_client_retourne_client(db, region_id):
    """create_client() doit retourner un objet Client avec un client_id."""
    client = crud.create_client(
        db,
        age=35,
        sexe="homme",
        imc=24.5,
        enfants=2,
        fumeur=False,
        region_id=region_id,
    )
    assert isinstance(client, Client)
    assert client.client_id is not None
    assert client.age == 35
    assert client.sexe == "homme"
    assert client.date_suppression is None


def test_create_client_email_telephone_nullable(db, region_id):
    """email et telephone doivent être None par défaut."""
    client = crud.create_client(
        db, age=40, sexe="femme", imc=22.0, enfants=0, fumeur=True, region_id=region_id
    )
    assert client.email is None
    assert client.telephone is None


# ── Tests get_client ───────────────────────────────────────────────────────────


def test_get_client_retourne_client(db, region_id):
    """get_client() doit retrouver le client par son PK."""
    client = crud.create_client(
        db, age=28, sexe="femme", imc=21.0, enfants=1, fumeur=False, region_id=region_id
    )
    trouve = crud.get_client(db, client.client_id)
    assert trouve is not None
    assert trouve.client_id == client.client_id


def test_get_client_inexistant_retourne_none(db):
    """get_client() doit retourner None pour un ID inexistant."""
    assert crud.get_client(db, 999999) is None


# ── Tests get_clients ──────────────────────────────────────────────────────────


def test_get_clients_actifs_only(db, region_id):
    """get_clients(actifs_only=True) ne doit pas retourner les clients supprimés."""
    client = crud.create_client(
        db, age=50, sexe="homme", imc=27.0, enfants=3, fumeur=False, region_id=region_id
    )
    crud.soft_delete_client(db, client.client_id)
    actifs = crud.get_clients(db, actifs_only=True)
    ids = [c.client_id for c in actifs]
    assert client.client_id not in ids


# ── Tests soft_delete_client ───────────────────────────────────────────────────


def test_soft_delete_client_definit_date_suppression(db, region_id):
    """soft_delete_client() doit définir date_suppression sans supprimer la ligne."""
    client = crud.create_client(
        db, age=45, sexe="femme", imc=25.0, enfants=0, fumeur=True, region_id=region_id
    )
    resultat = crud.soft_delete_client(db, client.client_id)
    assert resultat is not None
    assert resultat.date_suppression is not None
    # La ligne doit toujours exister en base
    encore_present = db.query(Client).filter_by(client_id=client.client_id).first()
    assert encore_present is not None


# ── Tests create_prediction ────────────────────────────────────────────────────


def test_create_prediction_retourne_prediction(db, region_id):
    """create_prediction() doit retourner un objet Prediction avec prediction_id."""
    client = crud.create_client(
        db, age=33, sexe="homme", imc=23.0, enfants=1, fumeur=False, region_id=region_id
    )
    pred = crud.create_prediction(
        db,
        client_id=client.client_id,
        cout_predit=12000.0,
        score_risque=0.75,
        categorie_risque="moyen",
        decision="accepter",
        prime=13800.0,
        version_modele="1.1.0",
    )
    assert isinstance(pred, Prediction)
    assert pred.prediction_id is not None
    assert pred.categorie_risque == "moyen"


def test_get_predictions_by_client(db, region_id):
    """get_predictions_by_client() doit retourner toutes les prédictions du client."""
    client = crud.create_client(
        db, age=38, sexe="femme", imc=28.0, enfants=2, fumeur=False, region_id=region_id
    )
    crud.create_prediction(
        db,
        client_id=client.client_id,
        cout_predit=8000.0,
        score_risque=0.60,
        categorie_risque="moyen",
        decision="accepter",
        prime=9200.0,
        version_modele="1.1.0",
    )
    crud.create_prediction(
        db,
        client_id=client.client_id,
        cout_predit=9000.0,
        score_risque=0.65,
        categorie_risque="moyen",
        decision="accepter",
        prime=10350.0,
        version_modele="1.1.0",
    )
    preds = crud.get_predictions_by_client(db, client.client_id)
    assert len(preds) == 2


# ── Tests create_contrat ───────────────────────────────────────────────────────


def test_create_contrat_retourne_contrat(db, region_id):
    """create_contrat() doit retourner un objet Contrat avec contrat_id."""
    from datetime import date

    client = crud.create_client(
        db, age=42, sexe="homme", imc=26.0, enfants=1, fumeur=False, region_id=region_id
    )
    contrat = crud.create_contrat(
        db,
        client_id=client.client_id,
        statut="actif",
        prime_mensuelle=250.0,
        date_debut=date(2026, 1, 1),
        type_couverture="standard",
    )
    assert isinstance(contrat, Contrat)
    assert contrat.contrat_id is not None
    assert contrat.prime_mensuelle == 250.0


# ── Tests create_sinistre ──────────────────────────────────────────────────────


def test_create_sinistre_retourne_sinistre(db, region_id):
    """create_sinistre() doit retourner un objet Sinistre avec sinistre_id."""
    from datetime import date

    client = crud.create_client(
        db, age=55, sexe="femme", imc=31.0, enfants=0, fumeur=True, region_id=region_id
    )
    contrat = crud.create_contrat(
        db,
        client_id=client.client_id,
        statut="actif",
        prime_mensuelle=400.0,
        date_debut=date(2026, 1, 1),
        type_couverture="premium",
    )
    sinistre = crud.create_sinistre(
        db,
        contrat_id=contrat.contrat_id,
        date_sinistre=date(2026, 3, 15),
        montant_sinistre=1500.0,
        type_sinistre="consultation",
    )
    assert isinstance(sinistre, Sinistre)
    assert sinistre.sinistre_id is not None
    assert sinistre.statut_sinistre == "en_cours"
