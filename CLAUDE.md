# AssuML Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-07

## Active Technologies
- Python 3.11 + Pandas 2.0+, NumPy, Matplotlib, Seaborn, Plotly Express, (002-exploration-feature-engineering)
- Fichiers CSV locaux (`data/small_data/insurance.csv` → `data/processed/features.csv`) (002-exploration-feature-engineering)

- **Backend**: Python 3.11, FastAPI 0.110+, Pydantic v2, SQLAlchemy 2.0+, Uvicorn
- **Frontend**: Streamlit 1.32+, Plotly Express
- **BDD**: PostgreSQL 15+, DuckDB 0.10+ (lecture seule Parquet)
- **ML**: scikit-learn 1.4+, Pandas 2.0+, NumPy, Joblib
- **ETL**: Requests, BeautifulSoup4 (scraping), OpenWeatherMap API
- **Tests**: pytest, pytest-asyncio, httpx
- **Qualité**: flake8, black (max-line-length=88)
- **CI/CD**: GitHub Actions, Docker, Docker Compose
- **Monitoring**: Prometheus-client, Grafana

## Project Structure

```text
AssuML/
├── data/small_data/insurance.csv        # Source ML (1 338 lignes)
├── data/big_data/insurance_big.parquet  # Big Data 10 M lignes (.gitignore)
├── notebooks/exploration.ipynb          # EDA + expérimentation ML
├── ml_models/training/                  # Scripts d'entraînement
├── ml_models/saved_models/             # .pkl + metadata.json (.gitignore)
├── ml_models/prediction/predict.py     # predict_cost(), predict_risk()
├── business/scoring.py                  # Calcul prime + décision
├── business/risk_engine.py              # Règles métier risque
├── data_pipeline/extract/               # csv_extractor, api_extractor, scraper
├── data_pipeline/transform/             # Transformations par source
├── data_pipeline/load/db_loader.py
├── api/main.py                          # FastAPI app (port 8000)
├── api/models/                          # SQLAlchemy ORM (7 tables)
├── api/schemas/                         # Pydantic schemas
├── api/routers/                         # Endpoints par domaine
├── streamlit_app/app.py                 # Streamlit (port 8501)
├── streamlit_app/pages/                 # 5 modules
├── database/schema.sql                  # DDL PostgreSQL
├── tests/unit/                          # Tests unitaires ML/business
├── tests/integration/                   # Tests API
├── tests/contract/                      # Tests contrats
├── monitoring/prometheus.yml
├── docker-compose.yml
└── .env                                 # Non commité — voir .env.example
```

## Commands

```bash
# Démarrage développement
uvicorn api.main:app --reload --port 8000
streamlit run streamlit_app/app.py --server.port 8501

# Entraînement ML
python ml_models/training/train_regression.py
python ml_models/training/train_classification.py

# ETL
python -m data_pipeline.extract.csv_extractor
python -m data_pipeline.extract.api_extractor
python -m data_pipeline.extract.scraper

# Big Data
python data_pipeline/generate_synthetic.py

# Tests
pytest tests/ -v
pytest --cov=. --cov-report=term-missing

# Qualité
flake8 . --max-line-length=88
black --check .

# Docker complet
docker compose up --build
```

## Code Style

- **Nommage fichiers**: anglais (PEP 8)
- **Nommage BDD**: français (tables, colonnes, variables métier)
- **Docstrings**: français
- **Commentaires**: français
- **Messages de commit**: français
- **Lint**: flake8 + black (max-line-length=88)
- Un fichier = une responsabilité (SRP)
- Jamais de credentials hardcodés — utiliser `.env`
- Jamais de `.pkl` ni `.parquet` committé (dans `.gitignore`)

## Règles architecture

- Streamlit → FastAPI → PostgreSQL (toujours via API pour les données relationnelles)
- Exception : `2_analytics.py` appelle DuckDB directement (lecture seule Parquet)
- Soft delete : `UPDATE clients SET date_suppression = NOW()` — jamais de DELETE physique
- Les modèles ML sont chargés une fois au démarrage FastAPI (singleton)
- Ports : API=8000, Streamlit=8501, Prometheus=9090, Grafana=3000, PostgreSQL=5432

## Recent Changes
- 002-exploration-feature-engineering: Added Python 3.11 + Pandas 2.0+, NumPy, Matplotlib, Seaborn, Plotly Express,

- 2026-04-07 — 001-assuml-souscription-ia: Initialisation complète du projet
  (stack Python, architecture 3 couches, 7 tables PostgreSQL, 2 modèles ML,
  Big Data DuckDB, ETL 3 sources, CI/CD GitHub Actions, monitoring Prometheus)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
