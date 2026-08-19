"""
Router météo — AssuML API.

Consultation des données météo collectées par le pipeline ETL (OpenWeatherMap).
Préfixe monté sur /api dans api/main.py.

Routes :
  GET /api/meteo — liste filtrée des données météo par région et/ou saison
"""

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import database.crud as crud
from api.dependencies import get_db
from api.schemas.meteo import MeteoRead

router = APIRouter(prefix="/meteo", tags=["meteo"])


@router.get("/", response_model=List[MeteoRead])
def lister_meteo(
    region: Optional[str] = None,
    saison: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    dernier_par_region: bool = False,
    db: Session = Depends(get_db),
):
    """Retourne les données météo avec filtres optionnels.

    Par défaut la route sert l'historique complet, du relevé le plus récent
    au plus ancien. Un client qui veut l'état courant d'une région, et non
    sa série, doit passer dernier_par_region=true.

    Args:
        region: Filtre sur nom_region (ex. 'southeast', 'northwest').
        saison: Filtre sur saison ('hiver', 'printemps', 'ete', 'automne').
        skip: Décalage pagination.
        limit: Nombre maximum de résultats.
        dernier_par_region: Ne retourne que le dernier relevé de chaque
            région, soit une ligne par région.
        db: Session SQLAlchemy injectée.

    Returns:
        Liste de MeteoRead.
    """
    return crud.get_donnees_meteo(
        db,
        region=region,
        saison=saison,
        skip=skip,
        limit=min(limit, 100),
        dernier_par_region=dernier_par_region,
    )
