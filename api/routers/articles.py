"""
Router articles — AssuML API.

Consultation des articles d'actualité scrappés par le pipeline ETL.
Préfixe monté sur /api dans api/main.py.

Routes :
  GET /api/articles — liste filtrée et paginée des articles
"""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import database.crud as crud
from api.dependencies import get_db
from api.schemas.article import ArticleListResponse

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/", response_model=ArticleListResponse)
def lister_articles(
    source: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Retourne la liste des articles scrappés, filtrables par source.

    Args:
        source: Filtre sur nom_source (correspondance exacte, ex. 'santemagazine.fr').
        skip: Décalage pagination.
        limit: Nombre maximum de résultats (max 100).
        db: Session SQLAlchemy injectée.

    Returns:
        ArticleListResponse avec items et total.
    """
    items, total = crud.get_articles(
        db, source=source, skip=skip, limit=min(limit, 100)
    )
    return ArticleListResponse(items=items, total=total)
