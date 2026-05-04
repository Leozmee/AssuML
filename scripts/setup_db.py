"""
Script d'initialisation complète de la base de données AssuML.

Étapes :
  1. Vérification de la connexion PostgreSQL
  2. Exécution de database/schema.sql (DROP + CREATE + INSERT regions)
  3. Chargement de 1 338 lignes depuis data/small_data/insurance.csv
  4. Rapport de validation

Idempotent : peut être exécuté plusieurs fois sans effet de bord.

Usage :
    python scripts/setup_db.py
"""

import sys
from pathlib import Path

# Ajouter la racine du projet au PYTHONPATH
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import psycopg2  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
import os  # noqa: E402
from sqlalchemy import text  # noqa: E402

from database.connection import engine  # noqa: E402
from database.load_csv import charger_csv  # noqa: E402

load_dotenv(ROOT / ".env")


def verifier_connexion() -> bool:
    """Vérifie que PostgreSQL est accessible avec les credentials du .env."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"Connexion PostgreSQL OK : {version[:50]}...")
        return True
    except Exception as e:
        print(f"Connexion PostgreSQL ECHEC : {e}")
        return False


def executer_schema(schema_path: Path) -> None:
    """Exécute le fichier schema.sql via psycopg2 (supporte les commandes DDL)."""
    conn_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASS"),
    }
    sql = schema_path.read_text(encoding="utf-8")

    conn = psycopg2.connect(**conn_params)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        print("Schéma SQL exécuté : 7 tables créées, 21 index créés.")
    finally:
        conn.close()


def rapport_validation() -> None:
    """Affiche un rapport de validation des tables principales."""
    with engine.connect() as conn:
        tables = ["regions", "clients", "predictions", "contrats", "sinistres"]
        print("\nRapport de validation :")
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))  # noqa: S608
            count = result.scalar()
            print(f"  {table:<15} : {count} ligne(s)")


def main() -> None:
    """Orchestration complète du setup de la base de données."""
    print("=" * 55)
    print("AssuML — Initialisation de la base de données")
    print("=" * 55)

    # Étape 1 : Connexion
    print("\n[1/4] Vérification de la connexion...")
    if not verifier_connexion():
        sys.exit(1)

    # Étape 2 : Schéma
    print("\n[2/4] Exécution du schéma SQL...")
    schema_path = ROOT / "database" / "schema.sql"
    executer_schema(schema_path)

    # Étape 3 : Chargement CSV
    print("\n[3/4] Chargement du CSV insurance.csv...")
    csv_path = ROOT / "data" / "small_data" / "insurance.csv"
    n = charger_csv(str(csv_path), verbose=True)

    # Étape 4 : Validation
    print("\n[4/4] Validation...")
    rapport_validation()

    print("\n" + "=" * 55)
    print(f"Setup terminé : {n} clients chargés avec succès.")
    print("=" * 55)


if __name__ == "__main__":
    main()
