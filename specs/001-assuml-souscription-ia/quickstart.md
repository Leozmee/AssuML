# Quickstart : AssuML — Guide de Démarrage Rapide

**Feature**: 001-assuml-souscription-ia
**Date**: 2026-04-07

---

## Prérequis

- Python 3.11+
- Docker + Docker Compose
- Git
- Clé API OpenWeatherMap (gratuite sur openweathermap.org)

---

## 1. Configuration initiale

```bash
# Cloner le dépôt et se placer sur la branche
git clone <repo-url>
cd AssuML
git checkout 001-assuml-souscription-ia

# Copier et remplir les variables d'environnement
cp .env.example .env
# Éditer .env : DATABASE_URL, OPENWEATHER_API_KEY, etc.

# Installer les dépendances Python
pip install -r requirements.txt
```

**Contenu de `.env.example`** :
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/assuml
OPENWEATHER_API_KEY=your_api_key_here
PYTHONPATH=.
```

---

## 2. Base de données PostgreSQL

```bash
# Lancer PostgreSQL via Docker
docker compose up -d db

# Créer la base et appliquer le schéma
docker compose exec db psql -U postgres -c "CREATE DATABASE assuml;"
psql $DATABASE_URL -f database/schema.sql

# Vérifier les 7 tables et les 4 régions
psql $DATABASE_URL -c "\dt"
psql $DATABASE_URL -c "SELECT * FROM regions;"
```

---

## 3. Entraînement des modèles ML

```bash
# Vérifier la présence du dataset
ls data/small_data/insurance.csv

# Entraîner la régression
python ml_models/training/train_regression.py

# Entraîner la classification
python ml_models/training/train_classification.py

# Vérifier les modèles et métadonnées
ls ml_models/saved_models/
# → regression.pkl, classification.pkl, metadata.json

cat ml_models/saved_models/metadata.json
```

**Résultats attendus** :
- Régression : R² ≥ 0.70 sur le test set
- Classification : accuracy ≥ 0.80 sur le test set

---

## 4. Pipeline ETL (sources de données)

```bash
# Extraction + transformation + chargement CSV
python -m data_pipeline.extract.csv_extractor

# Extraction météo (nécessite OPENWEATHER_API_KEY dans .env)
python -m data_pipeline.extract.api_extractor

# Scraping articles
python -m data_pipeline.extract.scraper

# Vérifier les données en base
psql $DATABASE_URL -c "SELECT COUNT(*) FROM donnees_meteo;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM articles;"
```

---

## 5. Génération du Big Data

```bash
# Générer 10 M lignes Parquet (à exécuter une seule fois)
python data_pipeline/generate_synthetic.py

# Vérifier
ls -lh data/big_data/insurance_big.parquet
python -c "import duckdb; print(duckdb.query(\"SELECT COUNT(*) FROM 'data/big_data/insurance_big.parquet'\").fetchone())"
# → (10000000,)
```

---

## 6. Lancer l'API FastAPI

```bash
# Développement (hot reload)
uvicorn api.main:app --reload --port 8000

# Vérifier l'API
curl http://localhost:8000/api/clients
# → {"total": 0, "clients": []}

# Documentation Swagger
open http://localhost:8000/docs
```

---

## 7. Tester le scoring ML via API

```bash
curl -X POST http://localhost:8000/api/predict/complet \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "sexe": "femme",
    "imc": 32.0,
    "enfants": 1,
    "fumeur": true,
    "region": "northeast"
  }'
# → {"cout_predit": ..., "categorie_risque": "eleve", "decision": "examiner", ...}
```

---

## 8. Lancer Streamlit

```bash
# Dans un second terminal
streamlit run streamlit_app/app.py --server.port 8501

# Ouvrir dans le navigateur
open http://localhost:8501
```

---

## 9. Lancer avec Docker Compose (environnement complet)

```bash
# Construire et lancer tous les services
docker compose up --build

# Services disponibles :
# - PostgreSQL    : localhost:5432
# - FastAPI       : http://localhost:8000 (Swagger: /docs)
# - Streamlit     : http://localhost:8501
# - Prometheus    : http://localhost:9090
# - Grafana       : http://localhost:3000 (admin/admin)
```

---

## 10. Lancer les tests

```bash
# Tests unitaires
pytest tests/unit/ -v

# Tests d'intégration (nécessite PostgreSQL actif)
pytest tests/integration/ -v

# Tests contrats API
pytest tests/contract/ -v

# Tous les tests + rapport de couverture
pytest --cov=. --cov-report=term-missing

# Lint
flake8 . --max-line-length=88
black --check .
```

---

## Validation rapide (smoke test)

```bash
# 1. Créer un client
curl -X POST http://localhost:8000/api/clients \
  -H "Content-Type: application/json" \
  -d '{"region":"southwest","age":35,"sexe":"homme","imc":28.5,"enfants":2,"fumeur":false}'

# 2. Scorer le client (utiliser le client_id retourné)
curl -X POST http://localhost:8000/api/predict/complet \
  -H "Content-Type: application/json" \
  -d '{"age":35,"sexe":"homme","imc":28.5,"enfants":2,"fumeur":false,"region":"southwest","client_id":1}'

# 3. Créer un contrat
curl -X POST http://localhost:8000/api/contrats \
  -H "Content-Type: application/json" \
  -d '{"client_id":1,"prime_mensuelle":300.0,"date_debut":"2026-04-07","type_couverture":"standard"}'

# 4. Vérifier les KPIs
curl http://localhost:8000/api/stats/kpis

# 5. Module Analytics Streamlit → ouvrir http://localhost:8501 → page Analytics
```
