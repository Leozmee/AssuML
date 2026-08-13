"""
Schémas Pydantic v2 pour les statistiques de santé régionales — AssuML API.

StatsRegionalesRead : statistiques d'une région retournées par l'API.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StatsRegionalesRead(BaseModel):
    """Statistiques de santé publique de l'État représentatif d'une région
    (CDC, NCHS, KFF, Census/ACS — cf. StatsRegionales)."""

    model_config = ConfigDict(from_attributes=True)

    stats_id: int
    region_id: int
    taux_obesite: float
    taux_tabagisme: float
    esperance_vie: float
    taux_diabete: float
    medecins_pour_100k: float
    taux_non_assures: float
    date_extraction: datetime
