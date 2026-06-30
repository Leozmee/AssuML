"""
Router clients — AssuML API.

Endpoints CRUD pour la gestion des clients assurés.
Préfixe monté sur /api/clients dans api/main.py.

Routes :
  GET    /api/clients           — liste paginée des clients actifs
  GET    /api/clients/{id}      — détail d'un client
  POST   /api/clients           — créer un client
  PUT    /api/clients/{id}      — modifier un client
  DELETE /api/clients/{id}      — soft delete (date_suppression)
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database.crud as crud
from api.dependencies import get_db
from api.schemas.client import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=List[ClientRead])
def lister_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Retourne la liste paginée des clients actifs (non supprimés).

    Args:
        skip: Décalage pagination.
        limit: Nombre maximum de résultats (max 100).
        db: Session SQLAlchemy injectée.

    Returns:
        Liste de ClientRead.
    """
    return crud.get_clients(db, skip=skip, limit=min(limit, 100))


@router.get("/{client_id}", response_model=ClientRead)
def obtenir_client(client_id: int, db: Session = Depends(get_db)):
    """Retourne le détail d'un client actif.

    Args:
        client_id: Identifiant du client.
        db: Session SQLAlchemy injectée.

    Returns:
        ClientRead si trouvé.

    Raises:
        HTTPException 404: Si le client est inexistant ou supprimé.
    """
    client = crud.get_client(db, client_id)
    if client is None or client.date_suppression is not None:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return client


@router.post("/", response_model=ClientRead, status_code=201)
def creer_client(body: ClientCreate, db: Session = Depends(get_db)):
    """Crée un nouveau client assuré.

    Args:
        body: Données de création (ClientCreate).
        db: Session SQLAlchemy injectée.

    Returns:
        ClientRead avec client_id généré.
    """
    client = crud.create_client(
        db,
        age=body.age,
        sexe=body.sexe,
        imc=body.imc,
        enfants=body.enfants,
        fumeur=body.fumeur,
        region_id=body.region_id,
        email=body.email,
        telephone=body.telephone,
        a_un_compte=body.a_un_compte,
    )
    return client


@router.put("/{client_id}", response_model=ClientRead)
def modifier_client(client_id: int, body: ClientUpdate, db: Session = Depends(get_db)):
    """Modifie les champs fournis d'un client actif.

    Args:
        client_id: Identifiant du client.
        body: Champs à modifier (tous optionnels).
        db: Session SQLAlchemy injectée.

    Returns:
        ClientRead mis à jour.

    Raises:
        HTTPException 404: Si le client est inexistant ou supprimé.
    """
    # Ne transmet que les champs explicitement fournis
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        client = crud.get_client(db, client_id)
        if client is None or client.date_suppression is not None:
            raise HTTPException(status_code=404, detail="Client introuvable")
        return client

    client = crud.update_client(db, client_id, **updates)
    if client is None:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return client


@router.delete("/{client_id}")
def supprimer_client(client_id: int, db: Session = Depends(get_db)):
    """Suppression logique d'un client (soft delete).

    Positionne date_suppression = maintenant sans DELETE physique.

    Args:
        client_id: Identifiant du client.
        db: Session SQLAlchemy injectée.

    Returns:
        Confirmation avec client_id.

    Raises:
        HTTPException 404: Si le client est inexistant ou déjà supprimé.
    """
    client = crud.soft_delete_client(db, client_id)
    if client is None:
        raise HTTPException(
            status_code=404, detail="Client introuvable ou déjà désactivé"
        )
    return {"message": "Client désactivé", "client_id": client_id}
