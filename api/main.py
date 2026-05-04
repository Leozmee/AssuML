"""
Point d'entrée de l'API REST FastAPI — AssuML.

Démarrage : uvicorn api.main:app --reload --port 8000
Documentation : http://localhost:8000/docs

Configuration :
  - Lifespan : chargement des modèles ML au démarrage (singletons)
  - CORS : autorisé pour http://localhost:8501 (Streamlit)
  - Routers : clients, contrats, sinistres, articles, meteo, ml, stats, health
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    articles,
    clients,
    contrats,
    health,
    meteo,
    ml,
    sinistres,
    stats,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gère le cycle de vie de l'application FastAPI.

    Au démarrage : charge les singletons ML pour éviter la latence au premier appel.
    À l'arrêt : aucune ressource à libérer (singletons garbage-collectés).
    """
    # Chargement des modèles ML au démarrage
    from ml_models.prediction.predict import _load_clf_pipeline, _load_pipeline

    try:
        _load_pipeline()
        _load_clf_pipeline()
        print("Modèles ML chargés avec succès.")
    except FileNotFoundError as e:
        print(f"AVERTISSEMENT : {e}")
        print("Les endpoints /predict/* ne seront pas disponibles.")

    yield
    # Rien à fermer au shutdown


app = FastAPI(
    title="AssuML API",
    description=(
        "API REST du système de prédiction d'assurance AssuML. "
        "Expose les endpoints CRUD clients, prédictions ML, "
        "contrats, sinistres, articles et données météo."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — autorisé pour l'application Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers
app.include_router(clients.router, prefix="/api")
app.include_router(contrats.router, prefix="/api")
app.include_router(sinistres.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(meteo.router, prefix="/api")
app.include_router(ml.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(health.router)


@app.get("/", tags=["root"])
def root() -> dict:
    """Point d'entrée racine — redirige vers la documentation."""
    return {
        "message": "AssuML API opérationnelle",
        "docs": "/docs",
        "health": "/health",
    }
