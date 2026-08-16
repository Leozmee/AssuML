"""
Connexion à la base de données PostgreSQL — AssuML.

Expose :
  - engine       : SQLAlchemy engine (psycopg2)
  - SessionLocal : factory de sessions SQLAlchemy
  - get_db()     : générateur de session (dépendance FastAPI)

Les credentials sont lus depuis le fichier .env via python-dotenv.
Aucun credential n'est hardcodé dans ce fichier.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Construit l'URL de connexion depuis les variables d'environnement
DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}"
    f"/{os.getenv('DB_NAME')}"
)

# Engine SQLAlchemy (connexion lazy — pas de connexion au chargement du module)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Vérifie la connexion avant chaque utilisation
)

# Factory de sessions — autocommit et autoflush désactivés (transaction explicite)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Générateur de session SQLAlchemy — dépendance FastAPI.

    Usage dans un endpoint FastAPI :
        def mon_endpoint(db: Session = Depends(get_db)):
            ...

    La session est automatiquement fermée après chaque requête,
    même en cas d'exception.

    Yields:
        Session: Session SQLAlchemy active.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
