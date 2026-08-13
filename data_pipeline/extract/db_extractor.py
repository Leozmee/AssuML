"""
Extracteur BDD externe — AssuML ETL.

Récupère les statistiques de santé régionales depuis la base de données
externe SQLite (data/external/stats_regionales.db — valeurs réelles CDC/
NCHS/KFF/Census pour l'État représentatif de chaque région, cf.
database/models.py::StatsRegionales) et les insère dans la table
stats_regionales de PostgreSQL.

Flux :
  1. Lecture de la BDD SQLite externe (SQLAlchemy — moteur distinct de
     PostgreSQL, démontre l'extraction depuis un SGBD externe)
  2. Lookup region_id depuis la table regions (PostgreSQL)
  3. Mapping nom_region -> region_id
  4. Insertion via db_loader
  5. Rapport

Usage standalone :
    python -m data_pipeline.extract.db_extractor
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Ajouter la racine du projet au PYTHONPATH
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from data_pipeline.load.db_loader import (  # noqa: E402
    compter_enregistrements,
    insert_stats_regionales,
)
from database.connection import SessionLocal  # noqa: E402
from database.models import Region  # noqa: E402

CHEMIN_SQLITE = ROOT / "data" / "external" / "stats_regionales.db"


def _build_region_lookup(db) -> dict[str, int]:
    """Construit le mapping nom_region → region_id depuis la table regions.

    Dupliqué depuis api_extractor.py plutôt qu'importé : les deux
    extracteurs restent des scripts indépendants (SRP — chacun responsable
    d'une seule source).

    Args:
        db: Session SQLAlchemy active.

    Returns:
        dict: {'southwest': 1, 'southeast': 2, ...}
    """
    regions = db.query(Region).all()
    return {r.nom_region: r.region_id for r in regions}


def lire_stats_sqlite(chemin_db: Path) -> list[dict]:
    """Lit la table de référence de la BDD SQLite externe.

    Fonction pure (pas d'accès PostgreSQL) — testable indépendamment avec
    un fichier SQLite temporaire.

    Args:
        chemin_db: Chemin vers le fichier SQLite.

    Returns:
        list[dict]: Une ligne par région (clés = colonnes de la table :
            nom_region, taux_obesite, taux_tabagisme, esperance_vie,
            taux_diabete, medecins_pour_100k, taux_non_assures).

    Raises:
        FileNotFoundError: Si le fichier SQLite n'existe pas.
    """
    if not chemin_db.exists():
        raise FileNotFoundError(f"BDD externe introuvable : {chemin_db}")

    engine = create_engine(f"sqlite:///{chemin_db}")
    with engine.connect() as conn:
        resultat = conn.execute(text("SELECT * FROM stats_regionales"))
        lignes = [dict(row._mapping) for row in resultat]
    return lignes


def mapper_region_id(records: list[dict], region_lookup: dict[str, int]) -> list[dict]:
    """Remplace nom_region par region_id dans chaque enregistrement.

    Fonction pure — testable indépendamment avec un lookup région factice.

    Args:
        records: Lignes brutes issues de lire_stats_sqlite() (avec nom_region).
        region_lookup: Mapping nom_region → region_id (table regions PostgreSQL).

    Returns:
        list[dict]: Mêmes lignes, avec region_id à la place de nom_region.
            Une région absente du lookup est silencieusement ignorée
            (pas d'erreur — cf. spec.md Edge Cases).
    """
    mappees = []
    for r in records:
        nom_region = r["nom_region"]
        if nom_region not in region_lookup:
            continue
        ligne = {k: v for k, v in r.items() if k != "nom_region"}
        ligne["region_id"] = region_lookup[nom_region]
        mappees.append(ligne)
    return mappees


def main() -> None:
    """Orchestration complète du pipeline BDD externe.

    Étapes :
      1. Lookup region_id depuis PostgreSQL
      2. Lecture de la BDD SQLite externe
      3. Mapping nom_region → region_id
      4. Insertion dans stats_regionales
      5. Rapport
    """
    print("=" * 50)
    print("ETL BDD externe — SQLite → stats_regionales")
    print("=" * 50)

    # Étape 1 : lookup region_id
    db = SessionLocal()
    try:
        region_lookup = _build_region_lookup(db)
    finally:
        db.close()

    print(f"\n[1/3] Régions chargées : {list(region_lookup.keys())}")

    # Étape 2 : lecture SQLite
    print("[2/3] Lecture de la BDD externe SQLite...")
    lignes_brutes = lire_stats_sqlite(CHEMIN_SQLITE)
    noms_regions = [ligne["nom_region"] for ligne in lignes_brutes]
    print(f"  {len(lignes_brutes)} ligne(s) lue(s) : {noms_regions}")

    # Étape 3 : mapping
    records = mapper_region_id(lignes_brutes, region_lookup)

    if not records:
        raise RuntimeError(
            "Aucune statistique régionale mappée — vérifier que les noms de "
            "région de la BDD externe correspondent à la table regions."
        )

    # Étape 4 : insertion
    n_inseres = insert_stats_regionales(records)
    print(f"[3/3] Insertion : {n_inseres} ligne(s) insérée(s) dans stats_regionales")

    # Rapport final
    total = compter_enregistrements("stats_regionales")
    print(f"\n  Total en base : {total} ligne(s) dans stats_regionales")
    print("=" * 50)


if __name__ == "__main__":
    main()
