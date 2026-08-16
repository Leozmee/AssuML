"""
Composants tableaux réutilisables — AssuML Streamlit.
"""

import pandas as pd
from typing import List

REGIONS_ID_TO_STR = {1: "Northeast", 2: "Northwest", 3: "Southeast", 4: "Southwest"}


def df_clients(clients: List[dict]) -> pd.DataFrame:
    """Construit un DataFrame formaté à partir de la liste de clients."""
    if not clients:
        return pd.DataFrame()
    rows = []
    for c in clients:
        rows.append(
            {
                "ID": c["client_id"],
                "Âge": c["age"],
                "Sexe": c["sexe"].capitalize(),
                "IMC": round(c["imc"], 1),
                "Enfants": c["enfants"],
                "Fumeur": "Oui" if c["fumeur"] else "Non",
                "Région": REGIONS_ID_TO_STR.get(c["region_id"], str(c["region_id"])),
                "Email": c.get("email") or "",
            }
        )
    return pd.DataFrame(rows)


def df_contrats(contrats: List[dict]) -> pd.DataFrame:
    """Construit un DataFrame formaté à partir de la liste de contrats."""
    if not contrats:
        return pd.DataFrame()
    rows = []
    for c in contrats:
        rows.append(
            {
                "ID contrat": c["contrat_id"],
                "Client ID": c["client_id"],
                "Type": c["type_couverture"].capitalize(),
                "Statut": c["statut"].capitalize(),
                "Prime/mois ($)": round(c["prime_mensuelle"], 2),
                "Début": c["date_debut"],
                "Fin": c.get("date_fin") or "—",
            }
        )
    return pd.DataFrame(rows)


def df_articles(articles: List[dict]) -> pd.DataFrame:
    """Construit un DataFrame pour l'affichage des articles."""
    if not articles:
        return pd.DataFrame()
    rows = []
    for a in articles:
        rows.append(
            {
                "ID": a["article_id"],
                "Titre": a["titre"],
                "Source": a["nom_source"],
                "Résumé": (a.get("resume") or "")[:120]
                + ("..." if len(a.get("resume") or "") > 120 else ""),
                "Publication": str(a.get("date_publication", ""))[:10],
                "URL": a["url_source"],
            }
        )
    return pd.DataFrame(rows)


def df_meteo(meteo: List[dict]) -> pd.DataFrame:
    """Construit un DataFrame météo par région et saison."""
    if not meteo:
        return pd.DataFrame()
    rows = []
    for m in meteo:
        rows.append(
            {
                "ID": m["meteo_id"],
                "Région": REGIONS_ID_TO_STR.get(m["region_id"], str(m["region_id"])),
                "Saison": m["saison"].capitalize(),
                "Temp. moy (°C)": round(m["temperature_moy"], 1),
                "Humidité moy (%)": round(m["humidite_moy"], 1),
                "Précipitations (mm)": round(m["precipitations"], 1),
                "Date collecte": str(m["date_collecte"])[:10],
            }
        )
    return pd.DataFrame(rows)
