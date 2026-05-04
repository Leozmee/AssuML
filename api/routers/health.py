"""
Router health check — AssuML API.

GET /health : vérifie l'état de l'API, de la base de données et des modèles ML.
"""

from fastapi import APIRouter
from sqlalchemy import text

from database.connection import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """Vérifie que l'API, la BDD et les modèles ML sont opérationnels.

    Returns:
        dict: Statut de chaque composant — 'ok' ou 'error'.
    """
    # Vérification base de données
    db_status = "ok"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    # Vérification modèles ML (singletons déjà chargés au démarrage)
    models_status = "ok"
    try:
        from ml_models.prediction.predict import _pipeline, _clf_pipeline

        if _pipeline is None or _clf_pipeline is None:
            models_status = "error"
    except Exception:
        models_status = "error"

    status = "ok" if db_status == "ok" and models_status == "ok" else "degraded"

    response = {"status": status, "database": db_status, "models": models_status}

    if status != "ok":
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail=response)

    return response
