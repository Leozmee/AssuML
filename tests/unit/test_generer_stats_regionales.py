"""Tests unitaires pour data/external/generer_stats_regionales.py."""

import sqlite3

from data.external.generer_stats_regionales import (
    STATS_PAR_REGION,
    VILLES_ETATS_REGIONS,
    generer,
)

REGIONS_ATTENDUES = {"southwest", "southeast", "northwest", "northeast"}

COLONNES_ATTENDUES = [
    "nom_region",
    "taux_obesite",
    "taux_tabagisme",
    "esperance_vie",
    "taux_diabete",
    "medecins_pour_100k",
    "taux_non_assures",
]


def test_villes_etats_regions_couvre_les_4_regions():
    """Le mapping ville/État doit couvrir exactement les 4 régions."""
    assert set(VILLES_ETATS_REGIONS.keys()) == REGIONS_ATTENDUES
    for infos in VILLES_ETATS_REGIONS.values():
        assert "ville" in infos and "etat" in infos


def test_stats_par_region_couvre_les_4_regions_et_6_champs():
    """Chaque région doit avoir exactement les 6 statistiques attendues."""
    assert set(STATS_PAR_REGION.keys()) == REGIONS_ATTENDUES
    champs_attendus = set(COLONNES_ATTENDUES) - {"nom_region"}
    for stats in STATS_PAR_REGION.values():
        assert set(stats.keys()) == champs_attendus


def test_generer_cree_fichier_sqlite_avec_4_lignes(tmp_path, monkeypatch):
    """generer() doit créer un fichier SQLite avec 4 lignes correctes."""
    import data.external.generer_stats_regionales as module

    chemin_test = tmp_path / "stats_regionales_test.db"
    monkeypatch.setattr(module, "CHEMIN_DB", chemin_test)

    generer()

    assert chemin_test.exists()
    conn = sqlite3.connect(chemin_test)
    try:
        cur = conn.execute("SELECT * FROM stats_regionales")
        colonnes = [c[0] for c in cur.description]
        lignes = cur.fetchall()
    finally:
        conn.close()

    assert colonnes == COLONNES_ATTENDUES
    assert len(lignes) == 4
    assert {ligne[0] for ligne in lignes} == REGIONS_ATTENDUES
