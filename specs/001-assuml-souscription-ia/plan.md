# Implementation Plan: AssuML — Système de Souscription Assurance Santé IA

**Branch**: `001-assuml-souscription-ia` | **Date**: 2026-04-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-assuml-souscription-ia/spec.md`

## Summary

Construire un système de souscription assurance santé alimenté par l'IA, capable
de scorer des clients via deux modèles ML (régression coût + classification risque),
de gérer le cycle de vie complet (CRUD clients/contrats/sinistres), de visualiser
des analytics sur 10 M lignes Big Data, et de monitorer les modèles et l'infrastructure.
L'architecture suit une séparation stricte des couches : Streamlit (UI) → FastAPI
(API REST) → PostgreSQL (données relationnelles), avec DuckDB (Parquet) en accès
direct depuis le module Analytics uniquement.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI 0.110+, Pydantic v2, SQLAlchemy 2.0+, Streamlit 1.32+,
  scikit-learn 1.4+, Pandas 2.0+, NumPy, Joblib, DuckDB 0.10+, Plotly Express,
  BeautifulSoup4, Requests, Prometheus-client
**Storage**: PostgreSQL 15+ (données relationnelles), Parquet (Big Data 10 M lignes,
  lecture seule via DuckDB)
**Testing**: pytest + pytest-asyncio + httpx (tests API)
**Target Platform**: Linux server (Docker), développement local macOS
**Project Type**: Web service (FastAPI REST) + Web application (Streamlit)
**Performance Goals**: Scoring IA < 500 ms, Analytics Big Data < 5 s, API CRUD < 200 ms p95
**Constraints**: RGPD (soft delete, PII nullable), clé API OpenWeatherMap gratuite (quota/jour),
  entraînement ML uniquement sur insurance.csv (1 338 lignes)
**Scale/Scope**: ~100 clients en base, 10 M lignes Parquet read-only, 2 modèles ML persistés

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Gate | Statut | Justification |
|----------|------|--------|---------------|
| I. Trois Sources de Données | 3 sources distinctes requises | ✅ | CSV (insurance.csv) + API (OpenWeatherMap) + Scraping (BeautifulSoup) |
| II. ML Rigoureux | Train/test split ≥ 70/30, deux modèles, metadata.json | ✅ | 2 modèles (.pkl) avec metadata, entraînement uniquement sur insurance.csv |
| III. Séparation des Couches | Streamlit → FastAPI → PostgreSQL ; DuckDB direct Analytics | ✅ | Architecture strictement respectée, exception Analytics documentée |
| IV. RGPD & Sécurité | Soft delete, PII nullable, pas de credentials hardcodés, pas de .pkl commités | ✅ | date_suppression, email/téléphone nullable, .env, .gitignore |
| V. Qualité & Testabilité | PEP8, pytest, docstrings français, 1 fichier = 1 responsabilité | ✅ | flake8/black, pytest, structure modulaire |

**Constitution Check Post-Design** (Phase 1) : ✅ Tous les gates passent. L'architecture
retenue et le schéma de données sont pleinement conformes à la constitution.

## Project Structure

### Documentation (this feature)

```text
specs/001-assuml-souscription-ia/
├── plan.md              # Ce fichier
├── research.md          # Phase 0 — choix techniques
├── data-model.md        # Phase 1 — entités et relations
├── quickstart.md        # Phase 1 — guide de démarrage rapide
├── contracts/           # Phase 1 — contrats API
│   ├── clients.md
│   ├── predictions.md
│   ├── contrats.md
│   ├── sinistres.md
│   └── donnees-externes.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
AssuML/
├── data/
│   ├── small_data/
│   │   └── insurance.csv              # Source ML (1 338 lignes)
│   ├── big_data/
│   │   └── insurance_big.parquet      # Big Data 10 M lignes (.gitignore)
│   └── external/
│       ├── api_data/                  # Données météo brutes
│       └── scraped_data/              # Articles bruts
│
├── notebooks/
│   └── exploration.ipynb              # EDA + expérimentation ML
│
├── ml_models/
│   ├── training/
│   │   ├── train_regression.py        # Entraînement modèle régression
│   │   └── train_classification.py    # Entraînement modèle classification
│   ├── saved_models/                  # (.gitignore)
│   │   ├── regression.pkl
│   │   ├── classification.pkl
│   │   └── metadata.json
│   └── prediction/
│       └── predict.py                 # predict_cost(), predict_risk()
│
├── business/
│   ├── scoring.py                     # Calcul prime + décision
│   └── risk_engine.py                 # Règles métier risque
│
├── data_pipeline/
│   ├── extract/
│   │   ├── csv_extractor.py           # Lecture insurance.csv
│   │   ├── api_extractor.py           # OpenWeatherMap
│   │   └── scraper.py                 # BeautifulSoup articles
│   ├── transform/
│   │   ├── transform_clients.py
│   │   ├── transform_meteo.py
│   │   └── transform_articles.py
│   ├── load/
│   │   └── db_loader.py               # Chargement PostgreSQL
│   └── generate_synthetic.py          # Génération Parquet 10 M lignes
│
├── api/
│   ├── main.py                        # FastAPI app, routes, CORS
│   ├── database.py                    # Connexion SQLAlchemy
│   ├── models/                        # Modèles SQLAlchemy (ORM)
│   │   ├── client.py
│   │   ├── prediction.py
│   │   ├── contrat.py
│   │   ├── sinistre.py
│   │   ├── region.py
│   │   ├── donnee_meteo.py
│   │   └── article.py
│   ├── schemas/                       # Schémas Pydantic
│   │   ├── client.py
│   │   ├── prediction.py
│   │   ├── contrat.py
│   │   ├── sinistre.py
│   │   └── donnees_externes.py
│   └── routers/                       # Endpoints par domaine
│       ├── clients.py
│       ├── predictions.py
│       ├── contrats.py
│       ├── sinistres.py
│       ├── articles.py
│       ├── meteo.py
│       └── stats.py
│
├── streamlit_app/
│   ├── app.py                         # Point d'entrée Streamlit
│   └── pages/
│       ├── 1_scoring.py               # Module Scoring
│       ├── 2_analytics.py             # Module Analytics (DuckDB direct)
│       ├── 3_crud.py                  # Module CRUD clients
│       ├── 4_monitoring.py            # Module Monitoring ML
│       └── 5_actualites.py            # Module Actualités
│
├── database/
│   └── schema.sql                     # DDL PostgreSQL (7 tables)
│
├── tests/
│   ├── unit/
│   │   ├── test_predict.py
│   │   ├── test_scoring.py
│   │   └── test_risk_engine.py
│   ├── integration/
│   │   ├── test_clients_api.py
│   │   ├── test_predictions_api.py
│   │   ├── test_contrats_api.py
│   │   └── test_sinistres_api.py
│   └── contract/
│       └── test_api_contracts.py
│
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│       └── dashboards/
│
├── .github/
│   └── workflows/
│       └── ci.yml                     # pytest + flake8 + black + Docker build
│
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.streamlit
├── .env.example
├── .gitignore                         # inclut *.pkl, *.parquet, .env
└── requirements.txt
```

**Structure Decision**: Architecture monorepo avec séparation claire des couches.
Tous les accès PostgreSQL passent par `api/`. Le module `streamlit_app/pages/2_analytics.py`
accède à DuckDB directement (exception documentée dans la constitution). Les modèles
ML sont isolés dans `ml_models/` et `business/`.

## Complexity Tracking

> Aucune violation de constitution détectée — section non applicable.

