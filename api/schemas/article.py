"""
Schémas Pydantic v2 pour les articles scrappés — AssuML API.

ArticleRead         : données d'un article retournées par l'API.
ArticleListResponse : réponse paginée avec total.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ArticleRead(BaseModel):
    """Données d'un article d'actualité."""

    model_config = ConfigDict(from_attributes=True)

    article_id: int
    titre: str
    url_source: str
    nom_source: str
    resume: Optional[str] = None
    image_url: Optional[str] = None
    date_publication: Optional[datetime] = None
    date_scraping: datetime


class ArticleListResponse(BaseModel):
    """Réponse liste d'articles avec total."""

    items: List[ArticleRead]
    total: int
