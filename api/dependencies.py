"""
Dépendances FastAPI partagées — AssuML API.

Fournit le générateur get_db() injecté via Depends() dans tous les routers
qui nécessitent un accès à la base de données PostgreSQL.
"""

from database.connection import SessionLocal


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
