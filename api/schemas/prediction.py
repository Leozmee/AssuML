"""
Schémas Pydantic v2 pour les prédictions ML — AssuML API.

PredictRequest          : entrée commune aux 3 endpoints ML.
PredictCoutResponse     : réponse de POST /predict/cout.
PredictRisqueResponse   : réponse de POST /predict/risque.
PredictCompletResponse  : réponse de POST /predict/complet.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Vecteur de caractéristiques pour la prédiction ML."""

    age: int = Field(..., ge=18, le=120)
    sexe: int = Field(..., ge=0, le=1, description="0=homme, 1=femme")
    imc: float = Field(..., ge=10.0, le=80.0)
    enfants: int = Field(..., ge=0, le=10)
    fumeur: int = Field(..., ge=0, le=1, description="0=non-fumeur, 1=fumeur")
    region: Literal["northeast", "northwest", "southeast", "southwest"]
    client_id: Optional[int] = Field(
        None, description="Si fourni dans predict/complet, la prédiction est persistée"
    )


class PredictCoutResponse(BaseModel):
    """Réponse de POST /predict/cout."""

    cout_predit: float = Field(..., description="Coût médical prédit en USD")


class PredictRisqueResponse(BaseModel):
    """Réponse de POST /predict/risque."""

    categorie_risque: str = Field(
        ..., description="Catégorie : faible, moyen, eleve ou critique"
    )
    score_risque: float = Field(
        ..., ge=0.0, le=1.0, description="Probabilité max (0–1)"
    )


class PredictCompletResponse(BaseModel):
    """Réponse de POST /predict/complet — orchestration complète."""

    cout_predit: float
    categorie_risque: str
    score_risque: float
    prime: float = Field(..., description="Prime d'assurance calculée en USD")
    decision: str = Field(
        ..., description="Décision de souscription : accepter, examiner ou refuser"
    )
    prediction_id: Optional[int] = Field(
        None, description="ID en base si persisté, None sinon"
    )
    deja_existante: bool = Field(
        False,
        description="True si la prédiction existait déjà en base (données inchangées)",
    )
