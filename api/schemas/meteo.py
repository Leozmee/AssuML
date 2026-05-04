"""
Schémas Pydantic v2 pour les données météo — AssuML API.

MeteoRead : données météo d'une collecte retournées par l'API.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MeteoRead(BaseModel):
    """Données météo d'une région pour une collecte donnée."""

    model_config = ConfigDict(from_attributes=True)

    meteo_id: int
    region_id: int
    temperature_moy: float
    humidite_moy: float
    precipitations: float
    saison: str
    date_collecte: datetime
