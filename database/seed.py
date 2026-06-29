"""
Script de peuplement initial de la base de données AssuML.

Insère les 4 régions et les 1 338 clients issus de insurance.csv au
démarrage Docker. Idempotent : si la base est déjà peuplée, le script
se termine sans rien insérer.

Usage :
    python database/seed.py

Constitution AssuML — Principes respectés :
    - Principe I  : utilise insurance.csv (source CSV obligatoire)
    - Principe III : accès direct PostgreSQL légitime (script d'admin)
    - Principe IV : credentials via variables d'environnement
    - Principe V  : docstrings français, PEP8, couverture pytest
"""

import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.exc import OperationalError

# Ajout de la racine du projet au path pour les imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import SessionLocal  # noqa: E402
from database.models import Client, Region  # noqa: E402

# ── Configuration du logger ───────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SEED] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────────

CHEMIN_CSV = Path("data/small_data/insurance.csv")

REGIONS = ["southwest", "southeast", "northwest", "northeast"]

MAPPING_SEXE = {"male": "homme", "female": "femme"}
MAPPING_FUMEUR = {"yes": True, "no": False}

CHUNK_SIZE = 500


# ── Fonctions de transformation ───────────────────────────────────────────────


def transformer_ligne(row: dict, regions_map: dict) -> dict:
    """Convertit une ligne du CSV brut en dict compatible avec le modèle Client.

    Args:
        row: Ligne du CSV sous forme de dict (colonnes anglaises Kaggle).
        regions_map: Dictionnaire {nom_region: region_id} issu de la BDD.

    Returns:
        dict: Dictionnaire prêt pour bulk_insert_mappings(Client, ...).

    Raises:
        ValueError: Si la région n'existe pas dans regions_map.
        ValueError: Si le sexe n'est pas dans les valeurs attendues.
    """
    region_str = str(row["region"]).strip().lower()
    if region_str not in regions_map:
        raise ValueError(
            f"Région inconnue : '{region_str}'. "
            f"Valeurs acceptées : {list(regions_map.keys())}"
        )

    sexe_str = str(row["sex"]).strip().lower()
    if sexe_str not in MAPPING_SEXE:
        raise ValueError(
            f"Sexe inconnu : '{sexe_str}'. "
            f"Valeurs acceptées : {list(MAPPING_SEXE.keys())}"
        )

    fumeur_str = str(row["smoker"]).strip().lower()
    if fumeur_str not in MAPPING_FUMEUR:
        raise ValueError(
            f"Valeur fumeur inconnue : '{fumeur_str}'. "
            f"Valeurs acceptées : {list(MAPPING_FUMEUR.keys())}"
        )

    return {
        "region_id": regions_map[region_str],
        "age": int(row["age"]),
        "sexe": MAPPING_SEXE[sexe_str],
        "imc": round(float(row["bmi"]), 2),
        "enfants": int(row["children"]),
        "fumeur": MAPPING_FUMEUR[fumeur_str],
        "email": None,
        "telephone": None,
    }


# ── Fonctions de seed ─────────────────────────────────────────────────────────


def seed_regions(session) -> int:
    """Insère les 4 régions dans la table regions si elle est vide.

    Args:
        session: Session SQLAlchemy active.

    Returns:
        int: Nombre de régions insérées (0 si déjà peuplée).
    """
    count = session.query(Region).count()
    if count > 0:
        logger.info("Régions déjà présentes (%d) — skip.", count)
        return 0

    session.bulk_insert_mappings(Region, [{"nom_region": r} for r in REGIONS])
    logger.info("4 régions insérées.")
    return 4


def seed_clients(session) -> int:
    """Lit insurance.csv et insère les 1 338 clients si la table est vide.

    Args:
        session: Session SQLAlchemy active.

    Returns:
        int: Nombre de clients insérés (0 si déjà peuplée).

    Raises:
        FileNotFoundError: Si CHEMIN_CSV est introuvable.
    """
    if not CHEMIN_CSV.exists():
        raise FileNotFoundError(
            f"Fichier CSV introuvable : {CHEMIN_CSV.resolve()}\n"
            "Vérifier que data/small_data/insurance.csv est présent."
        )

    count = session.query(Client).count()
    if count > 0:
        logger.info("Clients déjà présents (%d) — skip.", count)
        return 0

    # Chargement du lookup region → region_id
    regions_map = {r.nom_region: r.region_id for r in session.query(Region).all()}

    df = pd.read_csv(CHEMIN_CSV)
    records = []
    for _, row in df.iterrows():
        records.append(transformer_ligne(row.to_dict(), regions_map))

    # Insertion par chunks pour éviter les timeouts
    inseres = 0
    for i in range(0, len(records), CHUNK_SIZE):
        chunk = records[i : i + CHUNK_SIZE]
        session.bulk_insert_mappings(Client, chunk)
        inseres += len(chunk)

    logger.info("%d clients insérés.", inseres)
    return inseres


# ── Point d'entrée ────────────────────────────────────────────────────────────


def main() -> None:
    """Orchestre le seed : régions puis clients, dans une transaction unique."""
    session = SessionLocal()
    try:
        nb_regions = seed_regions(session)
        nb_clients = seed_clients(session)
        session.commit()

        if nb_regions == 0 and nb_clients == 0:
            logger.info("Base déjà peuplée, seed ignoré.")
        else:
            logger.info(
                "Seed terminé — %d région(s) insérée(s), %d client(s) inséré(s).",
                nb_regions,
                nb_clients,
            )

    except FileNotFoundError as exc:
        logger.error("CSV introuvable : %s", exc)
        session.rollback()
        sys.exit(1)

    except OperationalError as exc:
        logger.error("Base de données inaccessible : %s", exc)
        session.rollback()
        sys.exit(1)

    except Exception as exc:
        logger.error("Erreur inattendue : %s", exc)
        session.rollback()
        sys.exit(1)

    finally:
        session.close()


if __name__ == "__main__":
    main()
