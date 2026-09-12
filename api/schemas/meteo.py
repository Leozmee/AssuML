"""
Schémas Pydantic v2 pour les données météo — AssuML API.

MeteoRead : données météo d'une collecte retournées par l'API.
"""

from datetime import datetime
from typing import Optional

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
    # Moyennes glissantes sur 12 mois — None pour les collectes antérieures
    # à l'ajout de la qualité de l'air, ou si l'endpoint était indisponible.
    qualite_air_moy: Optional[float] = None
    pm25_moy: Optional[float] = None
    ozone_moy: Optional[float] = None
    date_collecte: datetime
