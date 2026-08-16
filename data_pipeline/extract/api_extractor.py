"""
Extracteur API OpenWeatherMap — AssuML ETL.

Récupère les données météo courantes pour les 4 régions US et les insère
dans la table donnees_meteo de PostgreSQL.

Flux :
  1. Lecture de la clé API depuis .env (OPENWEATHER_API_KEY)
  2. Lookup region_id depuis la table regions
  3. 4 appels API (une ville par région)
  4. Sauvegarde JSON brut dans data/external/api_data/
  5. Transformation via transform_meteo
  6. Insertion via db_loader

Usage standalone :
    python -m data_pipeline.extract.api_extractor
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# Ajouter la racine du projet au PYTHONPATH
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

from data_pipeline.load.db_loader import (  # noqa: E402
    compter_enregistrements,
    insert_donnees_meteo,
)
from data_pipeline.transform.transform_meteo import (  # noqa: E402
    transformer_reponse_api,
)
from database.connection import SessionLocal  # noqa: E402
from database.models import Region  # noqa: E402

# Mapping région (nom_region en DB) → ville pour l'API OpenWeatherMap
VILLES_REGIONS: dict[str, str] = {
    "southwest": "Phoenix,US",
    "southeast": "Atlanta,US",
    "northwest": "Seattle,US",
    "northeast": "Boston,US",
}

API_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
DOSSIER_BACKUP = ROOT / "data" / "external" / "api_data"


def _build_region_lookup(db) -> dict[str, int]:
    """Construit le mapping nom_region → region_id depuis la table regions.

    Args:
        db: Session SQLAlchemy active.

    Returns:
        dict: {'southwest': 1, 'southeast': 2, ...}
    """
    regions = db.query(Region).all()
    return {r.nom_region: r.region_id for r in regions}


def appeler_api(ville: str, api_key: str) -> dict:
    """Appelle l'endpoint current weather d'OpenWeatherMap pour une ville.

    Args:
        ville: Nom de la ville au format 'Ville,CODE_PAYS' (ex. 'Phoenix,US').
        api_key: Clé API OpenWeatherMap.

    Returns:
        dict: Réponse JSON brute de l'API.

    Raises:
        ValueError: Si la réponse HTTP n'est pas 200 (clé invalide, ville inconnue).
        requests.exceptions.RequestException: En cas d'erreur réseau.
    """
    params = {"q": ville, "appid": api_key, "units": "metric"}
    response = requests.get(API_BASE_URL, params=params, timeout=10)
    if response.status_code != 200:
        raise ValueError(
            f"Erreur API OpenWeatherMap pour '{ville}' : "
            f"HTTP {response.status_code} — {response.text[:200]}"
        )
    return response.json()


def sauvegarder_backup(data: list[dict], dossier: Path) -> str:
    """Sauvegarde les réponses API brutes dans un fichier JSON horodaté.

    Le fichier est créé AVANT toute insertion en base (safety net).

    Args:
        data: Liste de dicts (réponses JSON brutes + nom_region).
        dossier: Chemin du répertoire de backup.

    Returns:
        str: Chemin absolu du fichier créé.
    """
    dossier.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = dossier / f"meteo_{horodatage}.json"
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(chemin)


def main() -> None:
    """Orchestration complète du pipeline météo.

    Étapes :
      1. Validation de la clé API
      2. Lookup region_id depuis la BDD
      3. 4 appels API OpenWeatherMap
      4. Sauvegarde JSON horodatée
      5. Transformation (extraction champs, calcul saison)
      6. Insertion dans donnees_meteo
      7. Rapport
    """
    print("=" * 50)
    print("ETL Météo — OpenWeatherMap → donnees_meteo")
    print("=" * 50)

    # Étape 1 : clé API
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "OPENWEATHER_API_KEY absent ou vide dans .env. "
            "Créer un compte sur openweathermap.org et ajouter la clé."
        )

    # Étape 2 : lookup region_id
    db = SessionLocal()
    try:
        region_lookup = _build_region_lookup(db)
    finally:
        db.close()

    print(f"\n[1/4] Régions chargées : {list(region_lookup.keys())}")

    # Étape 3 : appels API
    reponses_brutes = []
    records_transformes = []
    erreurs = []

    print("[2/4] Appels API OpenWeatherMap...")
    for nom_region, ville in VILLES_REGIONS.items():
        try:
            reponse = appeler_api(ville, api_key)
            reponses_brutes.append({"nom_region": nom_region, "donnees": reponse})
            region_id = region_lookup[nom_region]
            record = transformer_reponse_api(reponse, region_id)
            records_transformes.append(record)
            print(
                f"  {nom_region:<12} ({ville:<12}) → "
                f"{record['temperature_moy']}°C, "
                f"{record['humidite_moy']}% humidité, "
                f"saison: {record['saison']}"
            )
        except (ValueError, requests.exceptions.RequestException) as e:
            erreurs.append(f"{ville}: {e}")
            print(f"  ERREUR {ville}: {e}")

    if not records_transformes:
        raise RuntimeError(
            "Aucune donnée météo récupérée — vérifier la clé API et la connexion."
        )

    # Étape 4 : sauvegarde backup
    chemin_backup = sauvegarder_backup(reponses_brutes, DOSSIER_BACKUP)
    print(f"\n[3/4] Backup sauvegardé : {chemin_backup}")

    # Étape 5 : insertion
    n_inseres = insert_donnees_meteo(records_transformes)
    print(f"[4/4] Insertion : {n_inseres} ligne(s) insérée(s) dans donnees_meteo")

    # Rapport final
    total = compter_enregistrements("donnees_meteo")
    print(f"\n  Total en base : {total} ligne(s) dans donnees_meteo")
    if erreurs:
        print(f"  Erreurs non bloquantes : {len(erreurs)}")
        for e in erreurs:
            print(f"    - {e}")
    print("=" * 50)


if __name__ == "__main__":
    main()
