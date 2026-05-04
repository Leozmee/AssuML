"""
Transformation des données météo OpenWeatherMap — AssuML ETL.

Fonctions :
  - determiner_saison()      : calcule la saison depuis le mois courant
  - transformer_reponse_api(): extrait les champs utiles d'une réponse JSON

Aucune dépendance à la base de données — module de transformation pur.
"""

# Mapping mois → saison (hémisphère nord, régions US)
SAISON_MAP: dict[int, str] = {
    1: "hiver",
    2: "hiver",
    3: "printemps",
    4: "printemps",
    5: "printemps",
    6: "ete",
    7: "ete",
    8: "ete",
    9: "automne",
    10: "automne",
    11: "automne",
    12: "hiver",
}


def determiner_saison(mois: int) -> str:
    """Détermine la saison depuis le numéro de mois (1-12).

    Utilise le calendrier météorologique de l'hémisphère nord :
      - Hiver : décembre, janvier, février
      - Printemps : mars, avril, mai
      - Été : juin, juillet, août
      - Automne : septembre, octobre, novembre

    Args:
        mois: Numéro de mois entre 1 et 12 inclus.

    Returns:
        str: Nom de la saison ('hiver', 'printemps', 'ete', 'automne').

    Raises:
        ValueError: Si mois n'est pas entre 1 et 12.
    """
    if mois not in SAISON_MAP:
        raise ValueError(f"Mois invalide : {mois}. Doit être entre 1 et 12.")
    return SAISON_MAP[mois]


def transformer_reponse_api(reponse_json: dict, region_id: int) -> dict:
    """Extrait et formate les champs météo depuis une réponse OpenWeatherMap.

    Champs extraits :
      - main.temp      → temperature_moy (°C, arrondi à 2 décimales)
      - main.humidity  → humidite_moy (%, float)
      - rain.1h        → precipitations (mm/h, 0.0 si absent = temps sec)

    La saison est calculée depuis le mois courant (datetime.now().month).

    Args:
        reponse_json: Dictionnaire JSON retourné par l'API OpenWeatherMap
                      (endpoint /data/2.5/weather).
        region_id: Identifiant FK vers la table regions.

    Returns:
        dict: Enregistrement prêt pour insert_donnees_meteo() avec les clés :
              region_id, temperature_moy, humidite_moy, precipitations, saison.

    Raises:
        KeyError: Si les champs 'main.temp' ou 'main.humidity' sont absents.
    """
    from datetime import datetime

    main = reponse_json["main"]
    temperature_moy = round(float(main["temp"]), 2)
    humidite_moy = float(main["humidity"])

    # La pluie est optionnelle — 0.0 si absent (temps sec)
    rain = reponse_json.get("rain", {})
    precipitations = round(float(rain.get("1h", 0.0)), 2)

    mois = datetime.now().month
    saison = determiner_saison(mois)

    return {
        "region_id": region_id,
        "temperature_moy": temperature_moy,
        "humidite_moy": humidite_moy,
        "precipitations": precipitations,
        "saison": saison,
    }
