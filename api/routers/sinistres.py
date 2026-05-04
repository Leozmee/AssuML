"""
Router sinistres — AssuML API.

Gestion des déclarations de sinistres. Vérification obligatoire que le contrat
est actif avant la création d'un sinistre.
Préfixe monté sur /api dans api/main.py.

Routes :
  GET /api/sinistres              — liste paginée (filtre ?contrat_id=)
  POST /api/sinistres             — déclarer un sinistre (contrat actif obligatoire)
  PUT /api/sinistres/{id}/statut  — modifier le statut de traitement
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database.crud as crud
from api.dependencies import get_db
from api.schemas.sinistre import SinistreCreate, SinistreRead, SinistreUpdate

router = APIRouter(prefix="/sinistres", tags=["sinistres"])


@router.get("/", response_model=List[SinistreRead])
def lister_sinistres(
    contrat_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Retourne la liste des sinistres, avec filtre optionnel par contrat.

    Args:
        contrat_id: Si fourni, filtre les sinistres de ce contrat.
        skip: Décalage pagination.
        limit: Nombre maximum de résultats.
        db: Session SQLAlchemy injectée.
    """
    return crud.get_sinistres(
        db, contrat_id=contrat_id, skip=skip, limit=min(limit, 100)
    )


@router.post("/", response_model=SinistreRead, status_code=201)
def declarer_sinistre(body: SinistreCreate, db: Session = Depends(get_db)):
    """Déclare un sinistre rattaché à un contrat actif.

    Règle métier : le contrat référencé DOIT avoir le statut 'actif'.
    Si le contrat est résilié, expiré, suspendu ou inexistant → 400.

    Args:
        body: Données du sinistre (SinistreCreate).
        db: Session SQLAlchemy injectée.

    Returns:
        SinistreRead avec sinistre_id généré et statut 'en_cours'.

    Raises:
        HTTPException 400: Si le contrat n'est pas actif.
        HTTPException 404: Si le contrat n'existe pas.
    """
    contrat = crud.get_contrat(db, body.contrat_id)
    if contrat is None:
        raise HTTPException(
            status_code=404,
            detail=f"Contrat {body.contrat_id} introuvable",
        )
    if contrat.statut != "actif":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Le contrat {body.contrat_id} n'est pas actif "
                f"(statut actuel : {contrat.statut})"
            ),
        )

    sinistre = crud.create_sinistre(
        db,
        contrat_id=body.contrat_id,
        date_sinistre=body.date_sinistre,
        montant_sinistre=body.montant_sinistre,
        type_sinistre=body.type_sinistre,
        description=body.description,
    )
    return sinistre


@router.put("/{sinistre_id}/statut", response_model=SinistreRead)
def modifier_statut_sinistre(
    sinistre_id: int,
    body: SinistreUpdate,
    db: Session = Depends(get_db),
):
    """Modifie le statut de traitement d'un sinistre.

    Args:
        sinistre_id: Identifiant du sinistre.
        body: Nouveau statut (SinistreUpdate).
        db: Session SQLAlchemy injectée.

    Returns:
        SinistreRead mis à jour.

    Raises:
        HTTPException 404: Si le sinistre n'existe pas.
    """
    sinistre = crud.update_sinistre_statut(db, sinistre_id, body.statut_sinistre)
    if sinistre is None:
        raise HTTPException(status_code=404, detail="Sinistre introuvable")
    return sinistre
