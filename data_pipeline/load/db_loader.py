"""
Couche de chargement générique — AssuML ETL.

Fournit des fonctions d'insertion réutilisables pour les sources externes :
  - insert_donnees_meteo()     : insère des lignes dans la table donnees_meteo
  - insert_stats_regionales()  : insère des lignes dans la table stats_regionales
  - insert_articles()          : insère des articles avec gestion des doublons
                                 (url_source UNIQUE)

Les insertions utilisent les modèles ORM de database/models.py et la session
SQLAlchemy de database/connection.py.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.connection import SessionLocal
from database.models import Article, DonneesMeteo, StatsRegionales


def insert_donnees_meteo(records: list[dict]) -> int:
    """Insère des enregistrements météo dans la table donnees_meteo.

    Chaque dict doit contenir les clés :
      region_id (int), temperature_moy (float), humidite_moy (float),
      precipitations (float), saison (str)

    La date_collecte est générée automatiquement (server_default).

    Args:
        records: Liste de dictionnaires représentant les lignes à insérer.

    Returns:
        int: Nombre de lignes insérées.
    """
    if not records:
        return 0

    db = SessionLocal()
    try:
        objets = [
            DonneesMeteo(
                region_id=r["region_id"],
                temperature_moy=r["temperature_moy"],
                humidite_moy=r["humidite_moy"],
                precipitations=r["precipitations"],
                saison=r["saison"],
            )
            for r in records
        ]
        db.add_all(objets)
        db.commit()
        return len(objets)
    finally:
        db.close()


def insert_stats_regionales(records: list[dict]) -> int:
    """Insère des enregistrements de statistiques régionales.

    Chaque dict doit contenir les clés :
      region_id (int), taux_obesite (float), taux_tabagisme (float),
      esperance_vie (float), taux_diabete (float),
      medecins_pour_100k (float), taux_non_assures (float)

    La date_extraction est générée automatiquement (server_default).

    Args:
        records: Liste de dictionnaires représentant les lignes à insérer.

    Returns:
        int: Nombre de lignes insérées.
    """
    if not records:
        return 0

    db = SessionLocal()
    try:
        objets = [
            StatsRegionales(
                region_id=r["region_id"],
                taux_obesite=r["taux_obesite"],
                taux_tabagisme=r["taux_tabagisme"],
                esperance_vie=r["esperance_vie"],
                taux_diabete=r["taux_diabete"],
                medecins_pour_100k=r["medecins_pour_100k"],
                taux_non_assures=r["taux_non_assures"],
            )
            for r in records
        ]
        db.add_all(objets)
        db.commit()
        return len(objets)
    finally:
        db.close()


def insert_articles(records: list[dict]) -> int:
    """Insère des articles dans la table articles en gérant les doublons.

    Utilise ON CONFLICT DO NOTHING sur url_source (contrainte UNIQUE).
    Un article dont l'URL existe déjà est silencieusement ignoré.

    Chaque dict doit contenir :
      titre (str), url_source (str), nom_source (str)
    Champs optionnels :
      resume (str | None), date_publication (datetime | None)

    Args:
        records: Liste de dictionnaires représentant les articles à insérer.

    Returns:
        int: Nombre de lignes effectivement insérées (doublons exclus).
    """
    if not records:
        return 0

    db = SessionLocal()
    try:
        lignes = [
            {
                "titre": r["titre"],
                "url_source": r["url_source"],
                "nom_source": r["nom_source"],
                "resume": r.get("resume"),
                "image_url": r.get("image_url"),
                "date_publication": r.get("date_publication"),
                "date_scraping": datetime.now(),
            }
            for r in records
        ]
        stmt = pg_insert(Article).values(lignes)
        stmt = stmt.on_conflict_do_nothing(index_elements=["url_source"])
        result = db.execute(stmt)
        db.commit()
        return result.rowcount if result.rowcount >= 0 else len(lignes)
    finally:
        db.close()


def compter_enregistrements(table: str) -> Optional[int]:
    """Retourne le nombre de lignes dans une table (pour validation).

    Args:
        table: Nom de la table PostgreSQL.

    Returns:
        int: Nombre de lignes, ou None en cas d'erreur.
    """
    from sqlalchemy import text
    from database.connection import engine

    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))  # noqa: S608
            return result.scalar()
    except Exception:
        return None
