"""
Schémas Pydantic v2 pour les clients — AssuML API.

ClientCreate : données requises pour créer un client.
ClientRead   : données retournées par l'API (inclut les champs générés).
ClientUpdate : mise à jour partielle (tous champs optionnels).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClientCreate(BaseModel):
    """Données requises pour créer un nouveau client."""

    nom: Optional[str] = Field(None, max_length=100)
    prenom: Optional[str] = Field(None, max_length=100)
    age: int = Field(..., ge=18, le=120, description="Âge de l'assuré (18–120)")
    sexe: str = Field(
        ..., pattern="^(homme|femme)$", description="Sexe : homme ou femme"
    )
    imc: float = Field(..., ge=10.0, le=80.0, description="Indice de masse corporelle")
    enfants: int = Field(..., ge=0, le=10, description="Nombre d'enfants à charge")
    fumeur: bool = Field(..., description="Statut fumeur")
    region_id: int = Field(
        ..., ge=1, le=4, description="Identifiant de la région (1–4)"
    )
    email: Optional[str] = Field(None, max_length=255)
    telephone: Optional[str] = Field(None, max_length=20)
    a_un_compte: bool = Field(
        False, description="Vrai si le client a un compte utilisateur"
    )


class ClientRead(BaseModel):
    """Données client retournées par l'API."""

    model_config = ConfigDict(from_attributes=True)

    client_id: int
    nom: Optional[str] = None
    prenom: Optional[str] = None
    age: int
    sexe: str
    imc: float
    enfants: int
    fumeur: bool
    region_id: int
    email: Optional[str] = None
    telephone: Optional[str] = None
    a_un_compte: bool = False
    date_creation: datetime
    date_suppression: Optional[datetime] = None
    date_modification: Optional[datetime] = None


class ClientUpdate(BaseModel):
    """Mise à jour partielle d'un client — tous les champs sont optionnels."""

    nom: Optional[str] = Field(None, max_length=100)
    prenom: Optional[str] = Field(None, max_length=100)
    age: Optional[int] = Field(None, ge=18, le=120)
    sexe: Optional[str] = Field(None, pattern="^(homme|femme)$")
    imc: Optional[float] = Field(None, ge=10.0, le=80.0)
    enfants: Optional[int] = Field(None, ge=0, le=10)
    fumeur: Optional[bool] = None
    region_id: Optional[int] = Field(None, ge=1, le=4)
    email: Optional[str] = Field(None, max_length=255)
    telephone: Optional[str] = Field(None, max_length=20)
