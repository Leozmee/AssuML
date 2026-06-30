"""
Router contrats — AssuML API.

Gestion des contrats d'assurance : liste, création et modification de statut.
Préfixe monté sur /api dans api/main.py.

Routes :
  GET /api/contrats                  — liste paginée (filtre ?client_id=)
  POST /api/contrats                 — créer un contrat
  PUT /api/contrats/{id}/statut      — modifier le statut
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database.crud as crud
from api.dependencies import get_db
from api.schemas.contrat import ContratCreate, ContratRead, ContratUpdate

router = APIRouter(prefix="/contrats", tags=["contrats"])


@router.get("/", response_model=List[ContratRead])
def lister_contrats(
    client_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Retourne la liste des contrats, avec filtre optionnel par client.

    Args:
        client_id: Si fourni, filtre les contrats de ce client.
        skip: Décalage pagination.
        limit: Nombre maximum de résultats.
        db: Session SQLAlchemy injectée.
    """
    return crud.get_contrats(db, client_id=client_id, skip=skip, limit=min(limit, 100))


@router.post("/", response_model=ContratRead, status_code=201)
def creer_contrat(body: ContratCreate, db: Session = Depends(get_db)):
    """Crée un contrat d'assurance pour un client actif.

    Args:
        body: Données du contrat (ContratCreate).
        db: Session SQLAlchemy injectée.

    Returns:
        ContratRead avec contrat_id généré et statut 'actif'.

    Raises:
        HTTPException 404: Si le client n'existe pas ou est inactif.
    """
    # Vérifier que le client existe et est actif
    client = crud.get_client(db, body.client_id)
    if client is None or client.date_suppression is not None:
        raise HTTPException(
            status_code=404,
            detail=f"Client {body.client_id} introuvable ou inactif",
        )
    contrat = crud.create_contrat(
        db,
        client_id=body.client_id,
        statut="actif",
        prime_mensuelle=body.prime_mensuelle,
        date_debut=body.date_debut,
        type_couverture=body.type_couverture,
        date_fin=body.date_fin,
    )
    return contrat


@router.put("/{contrat_id}/prime", response_model=ContratRead)
def modifier_prime_contrat(
    contrat_id: int,
    body: dict,
    db: Session = Depends(get_db),
):
    """Met à jour la prime mensuelle d'un contrat."""
    prime = body.get("prime_mensuelle")
    if prime is None or prime <= 0:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="prime_mensuelle invalide")
    contrat = crud.update_contrat_prime(db, contrat_id, prime)
    if contrat is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Contrat introuvable")
    return contrat


@router.put("/{contrat_id}/statut", response_model=ContratRead)
def modifier_statut_contrat(
    contrat_id: int,
    body: ContratUpdate,
    db: Session = Depends(get_db),
):
    """Modifie le statut d'un contrat existant.

    Args:
        contrat_id: Identifiant du contrat.
        body: Nouveau statut (ContratUpdate).
        db: Session SQLAlchemy injectée.

    Returns:
        ContratRead mis à jour.

    Raises:
        HTTPException 404: Si le contrat n'existe pas.
    """
    contrat = crud.update_contrat_statut(db, contrat_id, body.statut)
    if contrat is None:
        raise HTTPException(status_code=404, detail="Contrat introuvable")
    return contrat
