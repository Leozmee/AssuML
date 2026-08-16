"""
Chargement du CSV insurance.csv dans la table clients.

Délègue la transformation de chaque ligne à
`database.seed.transformer_ligne()` — la même fonction utilisée par le seed
Docker/CI (`database/seed.py`) — afin d'éviter toute divergence de règles de
mapping ou de validation entre les deux scripts de chargement.

La colonne `charges` du CSV n'est pas chargée en base (c'est la cible ML).

Idempotent : TRUNCATE + RESTART IDENTITY avant chaque chargement.
"""

from collections import Counter

import pandas as pd
from sqlalchemy import text

from database.connection import engine, SessionLocal
from database.models import Region
from database.seed import transformer_ligne

CSV_PATH = "data/small_data/insurance.csv"


def _build_region_lookup(db) -> dict[str, int]:
    """Construit un dictionnaire nom_region → region_id depuis la table regions."""
    regions = db.query(Region).all()
    return {r.nom_region: r.region_id for r in regions}


def charger_csv(csv_path: str = CSV_PATH, verbose: bool = True) -> int:
    """Charge les lignes du CSV insurance.csv dans la table clients.

    Effectue un TRUNCATE + RESTART IDENTITY pour garantir l'idempotence.
    Chaque ligne est transformée et validée par
    `database.seed.transformer_ligne()`.

    Args:
        csv_path: Chemin vers le fichier CSV source.
        verbose: Si True, affiche un rapport de chargement.

    Returns:
        int: Nombre de lignes insérées.
    """
    df = pd.read_csv(csv_path)

    db = SessionLocal()
    try:
        region_lookup = _build_region_lookup(db)

        rows = [
            transformer_ligne(row.to_dict(), region_lookup) for _, row in df.iterrows()
        ]

        # TRUNCATE idempotent — repart de 0
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE clients RESTART IDENTITY CASCADE"))

        insert_sql = text(
            """
            INSERT INTO clients
                (age, sexe, imc, enfants, fumeur, region_id, email, telephone)
            VALUES
                (:age, :sexe, :imc, :enfants, :fumeur, :region_id,
                 :email, :telephone)
            """
        )
        with engine.begin() as conn:
            conn.execute(insert_sql, rows)

        n_inserted = len(rows)

        if verbose:
            n_fumeurs = sum(r["fumeur"] for r in rows)
            pct_fumeurs = n_fumeurs / n_inserted if n_inserted else 0
            n_h = sum(1 for r in rows if r["sexe"] == "homme")
            n_f = sum(1 for r in rows if r["sexe"] == "femme")
            regions_count = Counter(r["region_id"] for r in rows)
            print(f"Chargement terminé : {n_inserted} clients insérés.")
            print(f"  Fumeurs       : {n_fumeurs} ({pct_fumeurs:.1%})")
            print(f"  Hommes/Femmes : {n_h} / {n_f}")
            print(f"  Régions       : {dict(regions_count)}")

        return n_inserted

    finally:
        db.close()


if __name__ == "__main__":
    charger_csv()
