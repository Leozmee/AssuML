"""
Génération de la BDD externe stats_regionales.db — AssuML.

Crée (ou régénère) data/external/stats_regionales.db : 4 lignes (une par
région fictive du dataset), chacune portant les statistiques de santé
publique réelles de l'État représentatif de cette région.

Correspondance ville/État : la même que celle déjà utilisée par le
pipeline météo (data_pipeline/extract/api_extractor.py::VILLES_REGIONS) —
une seule ville/État sert de référence pour toute la région. Ce découpage
en 4 régions (southwest/southeast/northwest/northeast) est propre au
dataset Kaggle insurance.csv : il n'existe dans aucune source fédérale
US (les vraies régions Census sont Northeast/Midwest/South/West). Les
valeurs ci-dessous ne sont donc PAS une moyenne régionale officielle,
seulement la statistique réelle de l'État représentatif.

Usage standalone :
    python data/external/generer_stats_regionales.py
"""

import sqlite3
from pathlib import Path

CHEMIN_DB = Path(__file__).resolve().parent / "stats_regionales.db"

# Même ville que api_extractor.py::VILLES_REGIONS, avec l'État correspondant
# (nécessaire pour les statistiques de santé, indisponibles par ville).
VILLES_ETATS_REGIONS: dict[str, dict[str, str]] = {
    "southwest": {"ville": "Phoenix,US", "etat": "Arizona"},
    "southeast": {"ville": "Atlanta,US", "etat": "Géorgie"},
    "northwest": {"ville": "Seattle,US", "etat": "Washington"},
    "northeast": {"ville": "Boston,US", "etat": "Massachusetts"},
}

# Statistiques réelles par État représentatif — une valeur par région,
# avec la source exacte de chaque champ commentée en regard.
STATS_PAR_REGION: dict[str, dict[str, float]] = {
    "southwest": {  # Arizona
        # CDC (BRFSS 2023, via World Population Review — obesity-rate-by-state)
        "taux_obesite": 33.3,
        # CDC (2024, via World Population Review — smoking-rates-by-state)
        "taux_tabagisme": 10.0,
        # NCHS — National Center for Health Statistics (2019, via Wikipedia
        # "List of U.S. states by life expectancy")
        "esperance_vie": 78.8,
        # CDC PLACES, niveau comté agrégé par État (via RHT Compass — diabetes)
        "taux_diabete": 13.9,
        # KFF (comptage médecins actifs, mai 2026) / population Census 2024
        # (7 582 384 hab.) — ratio recalculé, pas publié tel quel par KFF
        "medecins_pour_100k": 272.8,
        # Census/ACS 2023 (via World Population Review — uninsured-people-by-state)
        "taux_non_assures": 10.7,
    },
    "southeast": {  # Géorgie
        "taux_obesite": 35.4,
        "taux_tabagisme": 11.0,
        "esperance_vie": 77.4,
        "taux_diabete": 15.8,
        # KFF / population Census 2024 (~11,18 M hab., approximée)
        "medecins_pour_100k": 260.7,
        "taux_non_assures": 12.6,
    },
    "northwest": {  # Washington
        "taux_obesite": 31.5,
        "taux_tabagisme": 8.0,
        "esperance_vie": 80.0,
        "taux_diabete": 11.6,
        # KFF / population Census 2024 (7 958 180 hab.)
        "medecins_pour_100k": 307.2,
        "taux_non_assures": 6.4,
    },
    "northeast": {  # Massachusetts
        "taux_obesite": 27.0,
        "taux_tabagisme": 9.0,
        "esperance_vie": 80.4,
        "taux_diabete": 10.1,
        # KFF / population Census 2024 (~7,14 M hab., approximée)
        "medecins_pour_100k": 478.1,
        "taux_non_assures": 2.5,
    },
}


def generer() -> None:
    """Crée (ou remplace) le fichier SQLite avec les statistiques régionales.

    Le fichier est recréé à chaque exécution (DROP + CREATE) — usage
    ponctuel de mise à jour des valeurs, pas un ETL incrémental.
    """
    if CHEMIN_DB.exists():
        CHEMIN_DB.unlink()

    conn = sqlite3.connect(CHEMIN_DB)
    try:
        cur = conn.cursor()
        cur.execute(
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

        lignes = [
            (
                nom_region,
                stats["taux_obesite"],
                stats["taux_tabagisme"],
                stats["esperance_vie"],
                stats["taux_diabete"],
                stats["medecins_pour_100k"],
                stats["taux_non_assures"],
            )
            for nom_region, stats in STATS_PAR_REGION.items()
        ]
        cur.executemany("INSERT INTO stats_regionales VALUES (?,?,?,?,?,?,?)", lignes)
        conn.commit()

        print(f"BDD externe générée : {CHEMIN_DB}")
        for nom_region, infos in VILLES_ETATS_REGIONS.items():
            print(f"  {nom_region:<10} → {infos['etat']} ({infos['ville']})")
    finally:
        conn.close()


if __name__ == "__main__":
    generer()
