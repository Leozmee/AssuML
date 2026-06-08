"""
Dépendances FastAPI partagées — AssuML API.

Fournit :
  - get_db()        : session SQLAlchemy injectée dans les routers BDD
  - verify_api_key(): protection des routes sensibles par header X-API-Key
"""

import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from database.connection import SessionLocal

# APIKeyHeader expose un bouton "Authorize" dans Swagger (/docs)
# et lit automatiquement le header X-API-Key sur chaque requête.
_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db():
    """Génère une session SQLAlchemy et la ferme après chaque requête.

    Utilisé via Depends(get_db) dans les endpoints FastAPI.
    Garantit la fermeture de la session même en cas d'exception.

    Yields:
        Session: Session SQLAlchemy active.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(api_key: str = Security(_API_KEY_HEADER)) -> None:
    """Vérifie que le header X-API-Key correspond à la valeur dans .env.

    Injecter via dependencies=[Depends(verify_api_key)] sur include_router()
    pour protéger l'ensemble d'un router sans modifier chaque endpoint.

    Raises:
        HTTPException 500 : API_KEY absente des variables d'environnement.
        HTTPException 401 : clé fournie invalide ou header manquant.
    """
    expected = os.getenv("API_KEY")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API_KEY non configurée dans les variables d'environnement.",
        )
    if api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
