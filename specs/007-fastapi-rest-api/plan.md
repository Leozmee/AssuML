# Implementation Plan: API REST FastAPI complète

**Branch**: `007-fastapi-rest-api` | **Date**: 2026-05-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-fastapi-rest-api/spec.md`

## Summary

Créer l'API REST FastAPI complète dans `api/` avec 7 routers (clients, contrats, sinistres, articles, meteo, ml, stats), les schémas Pydantic v2, le chargement singleton des modèles ML, l'orchestration de la logique métier (scoring + décision), et la persistence optionnelle des prédictions. L'API est la porte d'entrée unique entre Streamlit et PostgreSQL (constitution §III).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI 0.110+, Pydantic v2, SQLAlchemy ORM 2.0+, Uvicorn, psycopg2-binary, python-dotenv
**Storage**: PostgreSQL 15+ local (`assuml_db`) — accès via SQLAlchemy ORM (`database/models.py`, `database/crud.py`)
**Testing**: pytest + httpx (tests contract API), pytest-asyncio
**Target Platform**: Serveur local macOS (développement), Linux (production Docker)
**Project Type**: web-service (API REST JSON)
**Performance Goals**: <500ms endpoints CRUD, <2s endpoint predict/complet
**Constraints**: CORS restreint à localhost:8501 (Streamlit), modèles .pkl chargés en singleton
**Scale/Scope**: 1 338 clients, 4 régions, ~15 articles, 8 lignes météo

## Constitution Check

| Principe | Statut | Détail |
|----------|--------|--------|
| I. 3 sources de données | ✅ PASS | L'API expose les données ETL (articles, meteo) sans modifier les sources |
| II. ML rigoureux | ✅ PASS | predict.py (singleton) est réutilisé, pas recréé — pas d'entraînement dans l'API |
| III. Séparation des couches | ✅ PASS | FastAPI = seule porte d'entrée PostgreSQL, Streamlit n'accède pas directement à la BDD |
| IV. RGPD et sécurité | ✅ PASS | Soft delete via date_suppression, pas de DELETE physique, credentials dans .env |
| V. Qualité et testabilité | ✅ PASS | SRP par fichier, docstrings en français, tests pytest prévus |

Aucune violation — pas de Complexity Tracking nécessaire.

## Project Structure

### Documentation (this feature)

```text
specs/007-fastapi-rest-api/
├── plan.md              # Ce fichier
├── research.md          # Décisions techniques
├── data-model.md        # Entités et relations
├── quickstart.md        # Scénarios de test
├── contracts/           # Contrats d'endpoints
│   ├── clients.md
│   ├── ml.md
│   ├── contrats.md
│   ├── sinistres.md
│   └── stats.md
└── tasks.md             # Généré par /speckit-tasks
```

### Source Code (repository root)

```text
api/
├── __init__.py
├── main.py                    # App FastAPI, CORS, lifespan, inclusion des routers
├── dependencies.py            # get_db() generator, get_models() singleton
├── routers/
│   ├── __init__.py
│   ├── clients.py             # GET /clients, GET /clients/{id}, POST, PUT, DELETE
│   ├── contrats.py            # GET /contrats, POST, PUT /contrats/{id}/statut
│   ├── sinistres.py           # GET /sinistres, POST (vérif contrat actif), PUT statut
│   ├── articles.py            # GET /articles (filtre ?source=)
│   ├── meteo.py               # GET /meteo (filtres ?region=&saison=)
│   ├── ml.py                  # POST /predict/cout, /predict/risque, /predict/complet
│   ├── stats.py               # GET /stats/kpis
│   └── health.py              # GET /health
├── schemas/
│   ├── __init__.py
│   ├── client.py              # ClientCreate, ClientRead, ClientUpdate
│   ├── contrat.py             # ContratCreate, ContratRead, ContratUpdate
│   ├── sinistre.py            # SinistreCreate, SinistreRead, SinistreUpdate
│   ├── prediction.py          # PredictRequest, PredictCoutResponse,
│   │                          # PredictRisqueResponse, PredictCompletResponse
│   ├── article.py             # ArticleRead, ArticleListResponse
│   └── meteo.py               # MeteoRead, MeteoListResponse
└── models/                    # Réexporte les modèles SQLAlchemy (symlink logique)
    └── __init__.py            # from database.models import *

database/
├── models.py                  # ORM existant (inchangé)
├── crud.py                    # CRUD existant — étendu avec fonctions contrats/sinistres
└── connection.py              # SessionLocal, engine (existant)

ml_models/prediction/
└── predict.py                 # Singleton existant — predict_cost(), predict_risk()

business/
├── scoring.py                 # calculer_prime() (existant)
└── risk_engine.py             # get_decision(), get_categorie_risque() (existant)

tests/
├── contract/
│   ├── test_clients.py        # Tests des endpoints clients via httpx
│   ├── test_ml.py             # Tests des endpoints predict/*
│   └── test_health.py        # Test /health
└── unit/
    └── test_schemas.py        # Validation Pydantic schemas
```

## Décisions d'architecture

### Chargement des modèles ML
Les modèles sont chargés via le mécanisme `lifespan` de FastAPI (contexte de vie de l'app) :
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup : déclenche le chargement des singletons predict.py
    from ml_models.prediction.predict import _load_pipeline, _load_clf_pipeline
    _load_pipeline()
    _load_clf_pipeline()
    yield
    # Shutdown : rien à fermer (singletons garbage-collectés)
```

### Orchestration predict/complet
```
POST /predict/complet
  → predict_cost(features) → cout_predit
  → predict_risk(features) → (categorie_risque, score_risque)
  → calculer_prime(cout_predit, categorie_risque) → prime
  → get_decision(categorie_risque) → decision
  → Si client_id fourni ET client existe → crud.create_prediction(...)
  → Retourne PredictCompletResponse
```

### Gestion des erreurs
- `404` : client, contrat ou sinistre non trouvé
- `400` : règle métier violée (sinistre sur contrat inactif, client_id inexistant)
- `422` : validation Pydantic (champs manquants, valeurs hors plage)
- `500` : modèle ML absent, BDD inaccessible

### Dépendances FastAPI
```python
# dependencies.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Complexity Tracking

Aucune violation constitutionnelle identifiée.
