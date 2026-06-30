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
