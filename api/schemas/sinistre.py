"""
Schémas Pydantic v2 pour les sinistres — AssuML API.

SinistreCreate : données requises pour déclarer un sinistre.
SinistreRead   : données retournées par l'API.
SinistreUpdate : mise à jour du statut de traitement.
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SinistreCreate(BaseModel):
    """Données requises pour déclarer un sinistre."""

    contrat_id: int = Field(..., description="Identifiant du contrat actif")
    date_sinistre: date
    montant_sinistre: float = Field(..., gt=0, description="Montant en USD")
    type_sinistre: Literal[
        "hospitalisation", "consultation", "pharmacie", "chirurgie", "urgence", "autre"
    ]
    description: Optional[str] = None


class SinistreRead(BaseModel):
    """Données sinistre retournées par l'API."""

    model_config = ConfigDict(from_attributes=True)

    sinistre_id: int
    contrat_id: int
    date_sinistre: date
    montant_sinistre: float
    type_sinistre: str
    statut_sinistre: str
    description: Optional[str] = None
    date_declaration: datetime


class SinistreUpdate(BaseModel):
    """Mise à jour du statut de traitement d'un sinistre."""

    statut_sinistre: Literal["en_cours", "accepte", "refuse", "rembourse"]
