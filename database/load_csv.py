"""
Chargement du CSV insurance.csv dans la table clients.

Mapping des colonnes CSV → colonnes PostgreSQL :
  sex      → sexe       : 'male'→'homme', 'female'→'femme'
  bmi      → imc        : float identique
  children → enfants    : integer identique
  smoker   → fumeur     : 'yes'→True, 'no'→False
  region   → region_id  : lookup dans la table regions (nom_region en anglais)

La colonne `charges` du CSV n'est pas chargée en base (c'est la cible ML).

Idempotent : TRUNCATE + RESTART IDENTITY avant chaque chargement.
"""

import pandas as pd
from sqlalchemy import text

from database.connection import engine, SessionLocal
from database.models import Region


# ── Constantes de mapping ──────────────────────────────────────────────────────

SEX_MAP = {"male": "homme", "female": "femme"}
SMOKER_MAP = {"yes": True, "no": False}
CSV_PATH = "data/small_data/insurance.csv"


def _build_region_lookup(db) -> dict[str, int]:
    """Construit un dictionnaire nom_region → region_id depuis la table regions."""
    regions = db.query(Region).all()
    return {r.nom_region: r.region_id for r in regions}


def charger_csv(csv_path: str = CSV_PATH, verbose: bool = True) -> int:
    """Charge les lignes du CSV insurance.csv dans la table clients.

    Effectue un TRUNCATE + RESTART IDENTITY pour garantir l'idempotence.
    Les clients sont insérés via psycopg2 execute_many pour la performance.

    Args:
        csv_path: Chemin vers le fichier CSV source.
        verbose: Si True, affiche un rapport de chargement.

    Returns:
        int: Nombre de lignes insérées.
    """
    # Lecture du CSV
    df = pd.read_csv(csv_path)

    db = SessionLocal()
    try:
        # Lookup region_id
        region_lookup = _build_region_lookup(db)

        # Transformation des colonnes
        df["sexe"] = df["sex"].map(SEX_MAP)
        df["imc"] = df["bmi"].astype(float)
        df["enfants"] = df["children"].astype(int)
        df["fumeur"] = df["smoker"].map(SMOKER_MAP)
        df["region_id"] = df["region"].map(region_lookup)

        # Vérification : toutes les régions ont été mappées
        unknown_regions = df[df["region_id"].isna()]["region"].unique()
        if len(unknown_regions) > 0:
            raise ValueError(
                f"Régions inconnues dans le CSV : {unknown_regions.tolist()}"
            )

        # Sélection des colonnes finales
        df_db = df[["sexe", "imc", "enfants", "fumeur", "region_id"]].copy()
        df_db["age"] = df["age"].astype(int)

        # TRUNCATE idempotent — repart de 0
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE clients RESTART IDENTITY CASCADE"))

        # Insertion en batch
        rows = df_db[["age", "sexe", "imc", "enfants", "fumeur", "region_id"]].to_dict(
            orient="records"
        )

        insert_sql = text(
            """
            INSERT INTO clients (age, sexe, imc, enfants, fumeur, region_id)
            VALUES (:age, :sexe, :imc, :enfants, :fumeur, :region_id)
            """
        )
        with engine.begin() as conn:
            conn.execute(insert_sql, rows)

        n_inserted = len(rows)

        if verbose:
            print(f"Chargement terminé : {n_inserted} clients insérés.")
            n_fumeurs = df_db["fumeur"].sum()
            pct_fumeurs = df_db["fumeur"].mean()
            print(f"  Fumeurs     : {n_fumeurs} ({pct_fumeurs:.1%})")
            n_h = (df_db["sexe"] == "homme").sum()
            n_f = (df_db["sexe"] == "femme").sum()
            print(f"  Hommes/Femmes : {n_h} / {n_f}")
            print(f"  Régions     : {df_db['region_id'].value_counts().to_dict()}")

        return n_inserted

    finally:
        db.close()


if __name__ == "__main__":
    charger_csv()
