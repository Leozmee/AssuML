# AssuML Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-06-13

## Contexte du projet
Vérifier le dossier `specs/` à la racine du projet et lire les fichiers correspondant à la branche git active.

## Active Technologies
- Python 3.11 + Pandas 2.0+, NumPy, Matplotlib, Seaborn, Plotly Express, (002-exploration-feature-engineering)
- Fichiers CSV locaux (`data/small_data/insurance.csv` → `data/processed/features.csv`) (002-exploration-feature-engineering)
- Python 3.11 + scikit-learn 1.4+, pandas 2.0+, numpy, joblib, matplotlib, seaborn (003-regression-model)
- fichiers CSV (entrée) + fichier `.pkl` (sortie sérialisée) — pas de base de données dans cette feature (003-regression-model)
- fichiers CSV (entrée) + `.pkl` (sortie) + `metadata.json` (traçabilité) — pas de BDD dans cette feature (004-classification-risk)
- Python 3.11 + SQLAlchemy 2.0+, psycopg2-binary, python-dotenv, pandas (005-postgres-db-setup)
- PostgreSQL 15+ local (Homebrew) — base `assuml_db`, user `assuml_user` (005-postgres-db-setup)
- Python 3.11 + requests 2.31+, beautifulsoup4 4.12+, sqlalchemy 2.0+ (déjà installé), pandas 2.0+, python-dotenv (déjà installé) (006-etl-pipeline)
- PostgreSQL 15+ local (`assuml_db`) + fichiers JSON locaux (`data/external/`) (006-etl-pipeline)
- Python 3.11 + FastAPI 0.110+, Pydantic v2, SQLAlchemy ORM 2.0+, Uvicorn, psycopg2-binary, python-dotenv (007-fastapi-rest-api)
- PostgreSQL 15+ local (`assuml_db`) — accès via SQLAlchemy ORM (`database/models.py`, `database/crud.py`) (007-fastapi-rest-api)
- Python 3.11 + NumPy, Pandas 2.0+, PyArrow, DuckDB, Plotly Express, Streamlit 1.32+ (009-bigdata-duckdb-parquet)
- Parquet (lecture seule) — PAS de PostgreSQL pour cette feature (009-bigdata-duckdb-parquet)
- Python 3.11 + SQLAlchemy 2.0+ (ORM existant), Pandas 2.0+, python-dotenv (011-seed-database)
- PostgreSQL 15+ — tables `regions` et `clients` uniquemen (011-seed-database)

- **Backend**: Python 3.11, FastAPI 0.110+, Pydantic v2, SQLAlchemy 2.0+, Uvicorn
- **Frontend principal**: Django 5.2+, Bootstrap 5, Plotly.js (port 8001)
- **Frontend POC**: Streamlit 1.32+, Plotly Express (port 8501 — conservé)
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
├── api/models/                          # SQLAlchemy ORM (6 tables)
├── api/schemas/                         # Pydantic schemas
├── api/routers/                         # Endpoints par domaine
├── django_app/                          # Django frontend principal (port 8001)
│   ├── config/                          # settings, urls, wsgi
│   ├── utils/api_client.py              # SEULE couche HTTP vers FastAPI
│   ├── accounts/                        # Auth double rôle admin/user
│   ├── scoring/ gestion/ analytics/     # 5 modules métier
│   └── monitoring/ actualites/
├── streamlit_app/app.py                 # Streamlit POC (port 8501 — conservé)
├── streamlit_app/pages/                 # 5 modules POC
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
python django_app/manage.py runserver 8001   # Frontend principal
streamlit run streamlit_app/app.py --server.port 8501  # POC uniquement

# Entraînement ML
python ml_models/training/train_regression.py
python ml_models/training/train_classification.py

# ETL
python -m data_pipeline.extract.csv_extractor
python -m data_pipeline.extract.api_extractor
python -m data_pipeline.extract.scraper

# Big Data
python big_data/generate_synthetic.py

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

- Django → FastAPI → PostgreSQL (frontend principal, toujours via API pour les données relationnelles)
- Streamlit → FastAPI → PostgreSQL (POC conservé, même règle)
- Exception unique Analytics : DuckDB appelé directement (lecture seule Parquet, performances 10 M lignes)
- `django_app/utils/api_client.py` est la SEULE couche qui parle à FastAPI depuis Django
- Soft delete : `UPDATE clients SET date_suppression = NOW()` — jamais de DELETE physique
- Les modèles ML sont chargés une fois au démarrage FastAPI (singleton)
- Ports : API=8000, Django=8001, Streamlit=8501 (POC), Prometheus=9090, Grafana=3000, PostgreSQL=5432

## Recent Changes
- 012-django-frontend-migration: Django 5.2 devient frontend principal (port 8001), Streamlit rétrogradé en POC
- predict-evol: Table `sinistres` supprimée → 6 tables PostgreSQL désormais
- predict-evol: Colonne `a_un_compte BOOLEAN DEFAULT FALSE` ajoutée à `clients`
- 011-seed-database: seed.py charge insurance.csv → table clients (1 338 lignes)
- 009-bigdata-duckdb-parquet: DuckDB + Parquet 10 M lignes pour Analytics

  (stack Python, architecture 3 couches, 6 tables PostgreSQL, 2 modèles ML,
  Big Data DuckDB, ETL 3 sources, CI/CD GitHub Actions, monitoring Prometheus)

<!-- MANUAL ADDITIONS START -->

## Architecture seed & flux métier scoring

### État initial de la base au `docker compose up`
| Table | Contenu au démarrage |
|---|---|
| `regions` | 4 lignes — déjà dans `schema.sql` |
| `clients` | 1 338 lignes — chargées par `database/seed.py` depuis `insurance.csv` |
| `predictions` | **vide** — remplie uniquement via l'endpoint `/predict/complet` |
| `contrats` | **vide** — créés par l'assureur via le module CRUD |

### Transformations insurance.csv → table clients
- `sex` : `female`→`femme`, `male`→`homme`
- `smoker` : `yes`→`True`, `no`→`False`
- `bmi` → `imc` (renommage)
- `children` → `enfants` (renommage)
- `region` → lookup `region_id` dans la table `regions`
- `charges` → **ignoré** (donnée du dataset ML, pas une prédiction produite par l'app)

### Flux métier scoring (NE PAS court-circuiter)
L'assureur ouvre Django (/gestion/ ou /scoring/) → sélectionne un client → clique "Scorer" → Django appelle FastAPI `/predict/complet` → les deux modèles ML tournent en direct → `business/scoring.py` calcule prime + décision → INSERT dans `predictions`.

Le même flux existe dans le POC Streamlit mais Django est l'interface de référence pour la soutenance.

Ne jamais pré-remplir `predictions` depuis un script. Le jury doit voir les modèles ML travailler en live.

### Source de vérité pour le seed
Toujours utiliser `data/small_data/insurance.csv` (CSV brut).
Ne pas utiliser `data/processed/features.csv` (format ML one-hot encodé, pas lisible en production).

<!-- MANUAL ADDITIONS END -->
