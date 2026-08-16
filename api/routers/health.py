"""
Router health check — AssuML API.

GET /health : vérifie l'état de l'API, de la base de données et des modèles ML.
"""

import json
from pathlib import Path

from fastapi import APIRouter
from sqlalchemy import text

from database.connection import engine

router = APIRouter(tags=["health"])

METADATA_PATH = (
    Path(__file__).resolve().parents[2] / "ml_models" / "saved_models" / "metadata.json"
)


def _lire_metadata() -> dict:
    """Lit metadata.json — source de vérité versionnée (committée en Git,
    contrairement aux .pkl) pour la version/métriques des modèles déployés."""
    try:
        with open(METADATA_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _resume_modele(meta: dict, cle: str) -> str:
    """Résume un bloc modèle ("regression" ou "classification") en une ligne
    lisible : "<Algorithme> (métrique clé)" — pas de numéro de version interne
    (metadata.json), sans intérêt pour un dashboard de monitoring.

    Gère l'ancien format v1.0.0 (régression au niveau racine, avant l'ajout
    de la classification) autant que le format v1.1.0+ (blocs imbriqués).
    """
    bloc = meta.get(cle)
    if bloc is None and cle == "regression" and "algorithme" in meta:
        bloc = meta  # ancien format plat, régression uniquement
    if not bloc:
        return "Non entraîné"

    algo = bloc.get("algorithme", "?")
    metriques = bloc.get("metriques_test", {})
    if cle == "regression":
        detail = f"R²={metriques['r2']}" if "r2" in metriques else ""
    else:
        detail = f"Accuracy={metriques['accuracy']}" if "accuracy" in metriques else ""

    return f"{algo}" + (f" ({detail})" if detail else "")


@router.get("/health")
def health_check() -> dict:
    """Vérifie que l'API, la BDD et les modèles ML sont opérationnels.

    Returns:
        dict: Statut de chaque composant ('ok'/'error') + version/métriques
        des modèles déployés (lues dans metadata.json, jamais interrogées
        auprès de MLflow — voir mlflow_gate.py : metadata.json est la source
        de vérité versionnée, MLflow sert au tracking/à la promotion, pas au
        service temps réel).
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

    metadata = _lire_metadata()
    response = {
        "status": status,
        "database": db_status,
        "models": models_status,
        "modele_regression": _resume_modele(metadata, "regression"),
        "modele_classification": _resume_modele(metadata, "classification"),
    }

    if status != "ok":
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail=response)

    return response
