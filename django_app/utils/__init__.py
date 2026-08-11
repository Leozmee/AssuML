"""Utilitaires partagés AssuML Django."""

# Mapping région nom ↔ region_id (correspond à l'ordre INSERT dans schema.sql)
REGION_ID_MAP = {
    "southwest": 1,
    "southeast": 2,
    "northwest": 3,
    "northeast": 4,
}

REGION_NOM_MAP = {v: k for k, v in REGION_ID_MAP.items()}


def region_nom_to_id(nom: str) -> int:
    """Convertit un nom de région en region_id (FK PostgreSQL)."""
    return REGION_ID_MAP[nom]


def region_id_to_nom(region_id: int) -> str:
    """Convertit un region_id en nom lisible."""
    return REGION_NOM_MAP.get(region_id, str(region_id))


def capitaliser_nom(valeur: str) -> str:
    """Met en majuscule la première lettre d'un nom/prénom (reste inchangé)."""
    valeur = (valeur or "").strip()
    return valeur[:1].upper() + valeur[1:] if valeur else valeur


def client_to_predict_payload(client: dict) -> dict:
    """Convertit un client (dict retourné par l'API) en payload /predict/*.

    Encode sexe/fumeur en 0/1 et la région en nom, au format attendu par
    PredictRequest côté FastAPI. N'inclut jamais client_id : à ajouter par
    l'appelant uniquement si la prédiction doit être persistée (cf.
    /predict/complet, qui ne sauvegarde que si client_id est fourni).
    """
    return {
        "age": client["age"],
        "sexe": 0 if client["sexe"] == "homme" else 1,
        "imc": float(client["imc"]),
        "enfants": client["enfants"],
        "fumeur": 1 if client["fumeur"] else 0,
        "region": region_id_to_nom(client["region_id"]),
    }
