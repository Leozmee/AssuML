"""
Router statistiques régionales — AssuML API.

Consultation des statistiques de santé régionales chargées par le pipeline
ETL (BDD externe SQLite, data/external/stats_regionales.db).
Préfixe monté sur /api dans api/main.py.

Routes :
  GET /api/stats-regionales — liste filtrée des statistiques régionales
"""

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import database.crud as crud
from api.dependencies import get_db
from api.schemas.stats_regionales import StatsRegionalesRead

router = APIRouter(prefix="/stats-regionales", tags=["stats-regionales"])


@router.get("/", response_model=List[StatsRegionalesRead])
def lister_stats_regionales(
    region: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Retourne les statistiques régionales avec filtre optionnel.

    Args:
        region: Filtre sur nom_region (ex. 'southeast', 'northwest').
        skip: Décalage pagination.
        limit: Nombre maximum de résultats.
        db: Session SQLAlchemy injectée.

    Returns:
        Liste de StatsRegionalesRead.
    """
    return crud.get_stats_regionales(
        db, region=region, skip=skip, limit=min(limit, 100)
    )
