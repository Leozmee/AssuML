"""Tests unitaires pour data_pipeline/extract/db_extractor.py.

Ne couvre que les fonctions pures (lire_stats_sqlite, mapper_region_id) —
aucune dépendance à PostgreSQL, un fichier SQLite temporaire suffit.
"""

import sqlite3
from pathlib import Path

import pytest

from data_pipeline.extract.db_extractor import lire_stats_sqlite, mapper_region_id


@pytest.fixture
def sqlite_fixture(tmp_path: Path) -> Path:
    """Crée une petite BDD SQLite avec le même schéma que stats_regionales.db."""
    chemin = tmp_path / "stats_regionales_test.db"
    conn = sqlite3.connect(chemin)
    conn.execute(
        """
        CREATE TABLE stats_regionales (
            nom_region TEXT PRIMARY KEY,
            taux_obesite REAL NOT NULL,
            taux_tabagisme REAL NOT NULL,
            esperance_vie REAL NOT NULL,
            taux_diabete REAL NOT NULL,
            medecins_pour_100k REAL NOT NULL,
            taux_non_assures REAL NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT INTO stats_regionales VALUES (?,?,?,?,?,?,?)",
        [
            ("southwest", 29.5, 14.0, 78.5, 10.5, 255.0, 15.5),
            ("southeast", 35.8, 19.5, 75.9, 13.2, 210.0, 13.0),
        ],
    )
    conn.commit()
    conn.close()
    return chemin


def test_lire_stats_sqlite_retourne_les_lignes(sqlite_fixture):
    """lire_stats_sqlite() doit retourner une liste de dicts, une par région."""
    lignes = lire_stats_sqlite(sqlite_fixture)
    assert len(lignes) == 2
    noms = {ligne["nom_region"] for ligne in lignes}
    assert noms == {"southwest", "southeast"}
    ligne_sw = next(row for row in lignes if row["nom_region"] == "southwest")
    assert ligne_sw["taux_obesite"] == 29.5


def test_lire_stats_sqlite_fichier_absent_leve_erreur(tmp_path: Path):
    """lire_stats_sqlite() lève une erreur explicite si le fichier n'existe pas."""
    chemin_absent = tmp_path / "inexistant.db"
    with pytest.raises(FileNotFoundError):
        lire_stats_sqlite(chemin_absent)


def test_mapper_region_id_remplace_nom_region():
    """mapper_region_id() doit remplacer nom_region par region_id."""
    records = [
        {"nom_region": "southwest", "taux_obesite": 29.5},
        {"nom_region": "southeast", "taux_obesite": 35.8},
    ]
    lookup = {"southwest": 1, "southeast": 2, "northwest": 3, "northeast": 4}

    mappees = mapper_region_id(records, lookup)

    assert len(mappees) == 2
    assert all("nom_region" not in r for r in mappees)
    sw = next(r for r in mappees if r["region_id"] == 1)
    assert sw["taux_obesite"] == 29.5


def test_mapper_region_id_ignore_region_absente_du_lookup():
    """mapper_region_id() doit ignorer silencieusement une région inconnue."""
    records = [
        {"nom_region": "southwest", "taux_obesite": 29.5},
        {"nom_region": "region_inconnue", "taux_obesite": 40.0},
    ]
    lookup = {"southwest": 1}

    mappees = mapper_region_id(records, lookup)

    assert len(mappees) == 1
    assert mappees[0]["region_id"] == 1
