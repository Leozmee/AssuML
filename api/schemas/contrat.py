"""
Schémas Pydantic v2 pour les contrats d'assurance — AssuML API.

ContratCreate : données requises pour créer un contrat.
ContratRead   : données retournées par l'API.
ContratUpdate : mise à jour du statut d'un contrat.
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ContratCreate(BaseModel):
    """Données requises pour créer un contrat d'assurance."""

    client_id: int = Field(..., description="Identifiant du client assuré")
    prime_mensuelle: float = Field(..., gt=0, description="Prime mensuelle en USD")
    date_debut: date = Field(..., description="Date de début du contrat")
    type_couverture: Literal["basique", "standard", "premium", "famille"]
    date_fin: Optional[date] = None


class ContratRead(BaseModel):
    """Données contrat retournées par l'API."""

    model_config = ConfigDict(from_attributes=True)

    contrat_id: int
    client_id: int
    statut: str
    prime_mensuelle: float
    date_debut: date
    date_fin: Optional[date] = None
    type_couverture: str
    date_creation: datetime


class ContratUpdate(BaseModel):
    """Mise à jour du statut d'un contrat."""

    statut: Literal["actif", "resilie", "expire", "suspendu"]
