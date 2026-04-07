# Research: AssuML — Choix Techniques et Décisions d'Architecture

**Feature**: 001-assuml-souscription-ia
**Date**: 2026-04-07
**Statut**: Complet — aucun NEEDS CLARIFICATION résiduel

---

## 1. Architecture Générale

**Decision**: Monorepo avec séparation stricte des couches (ML / ETL / API / Frontend).

**Rationale**: Un seul dépôt facilite la gestion CI/CD pour un développeur solo.
La séparation par couches permet de tester chaque composant indépendamment et
de valider chaque compétence Simplon distinctement.

**Alternatives considered**:
- Microservices séparés : over-engineering pour un développeur solo, complexité
  réseau injustifiée.
- Tout dans un seul module Python : impossible à tester par couche, ne démontre
  pas la séparation des responsabilités.

---

## 2. Base de Données : PostgreSQL avec SQLAlchemy ORM

**Decision**: PostgreSQL 15+ avec SQLAlchemy 2.0 (ORM async-capable) + Alembic
pour les migrations.

**Rationale**: PostgreSQL est le standard production pour les systèmes transactionnels.
SQLAlchemy ORM permet de valider les entités côté Python avant persistence. Les
contraintes CHECK et FK sont définies au niveau DDL (`schema.sql`) pour garantir
l'intégrité sans dépendre de l'ORM seul.

**Alternatives considered**:
- SQLite : pas de contraintes CHECK avancées, pas adapté production.
- MongoDB : pas de FK ni contraintes relationnelles, ne valide pas les compétences
  SQL de la certification.

**Key decisions**:
- Soft delete via `date_suppression TIMESTAMP NULL` — conformité RGPD.
- `email` et `telephone` nullable — collecte optionnelle.
- 20 index : FK systématiques + index partiels (`WHERE date_suppression IS NULL`)
  pour les requêtes sur clients actifs.
- 22 contraintes CHECK : ages 18–120, IMC 10–80, score_risque 0–1,
  montant_sinistre > 0, etc.
- 5 FK avec ON DELETE CASCADE : sinistres cascade depuis contrats,
  prédictions/contrats cascade depuis clients.

---

## 3. API REST : FastAPI + Pydantic v2

**Decision**: FastAPI 0.110+ avec Pydantic v2 pour la validation et la génération
automatique du schéma OpenAPI (Swagger `/docs`).

**Rationale**: FastAPI offre la meilleure performance async Python pour les APIs
REST. Pydantic v2 valide les entrées avant qu'elles atteignent la BDD (double
validation avec les contraintes PostgreSQL). La génération automatique Swagger
satisfait l'exigence de documentation de la certification.

**Alternatives considered**:
- Django REST Framework : plus verbeux, pas async-native, moins adapté aux APIs
  ML légères.
- Flask : pas de validation intégrée, pas de génération OpenAPI automatique.

**Key decisions**:
- Schémas Pydantic séparés par opération : `ClientCreate`, `ClientRead`,
  `ClientUpdate` → évite de mixer les champs obligatoires/optionnels.
- Soft delete implémenté dans le router `DELETE /api/clients/{id}` :
  `UPDATE clients SET date_suppression = NOW()`.
- Les endpoints ML (`/api/predict/*`) appellent `predict.py` qui charge les
  modèles `.pkl` en mémoire au démarrage de l'API (singleton pattern).

---

## 4. Machine Learning : scikit-learn avec deux modèles distincts

**Decision**: Deux pipelines indépendants avec `scikit-learn Pipeline` :
régression (RandomForestRegressor) et classification (RandomForestClassifier)
comme algorithmes retenus après comparaison.

**Rationale**: RandomForest est robuste aux outliers et non-linéarités présents
dans insurance.csv (distribution des charges très asymétrique, impact fumeur
non linéaire). La comparaison avec LinearRegression et GradientBoosting est
documentée dans le notebook `exploration.ipynb`.

**Alternatives considered**:
- LinearRegression seule : R² ≈ 0.12 (age/bmi/children seulement),
  R² ≈ 0.75 avec toutes les variables — acceptable mais sous-optimal vs RF.
- GradientBoosting : performances similaires à RF mais temps d'entraînement
  plus long, moins explicable pour la soutenance.

**Key decisions**:
- Encodage : `smoker` (yes→1, no→0), `sex` (female→1, male→0), `region`
  one-hot avec `drop_first=True` (northeast comme référence).
- Pipeline sklearn : `StandardScaler` + estimateur → évite la fuite de
  données (fit uniquement sur train).
- `train_test_split(test_size=0.3, random_state=42)`.
- `metadata.json` : version, date_entrainement, r2_train, r2_test, mae, rmse
  (régression) ; accuracy, f1_macro, classes (classification).
- Les modèles sont chargés une seule fois au démarrage de FastAPI.

**Catégories de risque** (seuils sur `charges` en USD du dataset Kaggle) :
- faible : charges < 5 000
- moyen : 5 000 ≤ charges < 15 000
- élevé : 15 000 ≤ charges < 30 000
- critique : charges ≥ 30 000

**Règle prime mensuelle** : `prime = cout_predit / 12 × coefficient_risque`
où `coefficient_risque` = {faible: 1.0, moyen: 1.15, élevé: 1.35, critique: 1.60}.

---

## 5. Big Data : DuckDB + Parquet

**Decision**: DuckDB 0.10+ en lecture seule sur un fichier Parquet de 10 M
lignes, appelé directement depuis Streamlit (module Analytics).

**Rationale**: DuckDB est optimisé pour les requêtes analytiques sur Parquet
(columnar storage, predicate pushdown). Les performances < 5 s pour 10 M lignes
sont atteignables sans serveur dédié. L'appel direct depuis Streamlit (sans
passer par FastAPI) est l'exception documentée dans la constitution.

**Alternatives considered**:
- Spark : over-engineering, nécessite un cluster ou Spark local lourd.
- PostgreSQL avec COPY : PostgreSQL n'est pas optimisé pour 10 M lignes en
  lecture analytique non indexée.

**Génération Big Data** : `generate_synthetic.py` utilise les distributions
statistiques du dataset Kaggle (mean, std, proportions) pour générer 10 M
lignes réalistes en Parquet. Colonnes supplémentaires : `charges_log`,
`age_group`, `bmi_category`, `risk_score`.

---

## 6. Frontend : Streamlit + Plotly Express

**Decision**: Streamlit 1.32+ avec navigation multipage (`pages/`) et
graphiques Plotly Express (interactifs, zoomables, filtrables).

**Rationale**: Streamlit permet de construire des dashboards IA en Python pur,
sans HTML/CSS. Plotly Express offre l'interactivité (hover, zoom, filtre)
requise pour le module Analytics. Les 5 modules sont isolés dans des fichiers
de pages séparés.

**Key decisions**:
- Module Analytics (`2_analytics.py`) : appel DuckDB direct (exception constitution).
- Tous les autres modules passent par `requests.get/post` vers `http://localhost:8000`.
- `st.session_state` pour persister les sélections entre reruns Streamlit.

---

## 7. ETL : Pipeline Python en trois étapes

**Decision**: Pipeline ETL structuré en `extract/`, `transform/`, `load/`
exécutable en CLI (`python -m data_pipeline.run`).

**Rationale**: La séparation Extract/Transform/Load est la bonne pratique ETL
standard. Chaque extracteur est indépendant et peut être testé/exécuté seul.

**Sources** :
- `csv_extractor.py` : lecture `insurance.csv` → DataFrame Pandas.
- `api_extractor.py` : appel OpenWeatherMap (endpoint `/data/2.5/weather`
  pour chaque région mappée à une ville US représentative), stockage JSON dans
  `data/external/api_data/`.
- `scraper.py` : scraping BeautifulSoup sur sources publiques (ex. argus.fr,
  assurance.com), stockage HTML/JSON dans `data/external/scraped_data/`.

**Mapping régions → villes US** (OpenWeatherMap) :
- southwest → Phoenix, AZ
- southeast → Atlanta, GA
- northwest → Seattle, WA
- northeast → Boston, MA

---

## 8. CI/CD : GitHub Actions + Docker

**Decision**: Pipeline GitHub Actions avec 3 jobs séquentiels : lint (flake8 +
black check), tests (pytest), build Docker.

**Rationale**: GitHub Actions est natif à GitHub (pas d'infra supplémentaire),
gratuit pour les dépôts publics. Docker garantit la reproductibilité des
environnements dev/prod.

**Key decisions**:
- `Dockerfile.api` : image Python 3.11-slim, expose le port 8000.
- `Dockerfile.streamlit` : image Python 3.11-slim, expose le port 8501.
- `docker-compose.yml` : services `db` (postgres:15), `api`, `streamlit`,
  `prometheus`, `grafana` avec un réseau Docker interne.
- Variables d'environnement via `.env` (non commité), `.env.example` commité.
- `.gitignore` : `*.pkl`, `*.parquet`, `.env`, `__pycache__/`.

---

## 9. Monitoring : Prometheus + Grafana

**Decision**: Prometheus scrape les métriques exposées par FastAPI via
`prometheus-client` (`/metrics` endpoint). Grafana affiche les dashboards.

**Rationale**: Prometheus + Grafana est le standard industrie pour le monitoring
d'APIs Python. Pas de tables de logs dans PostgreSQL (constitution).

**Métriques exposées** :
- Infra : `http_requests_total`, `http_request_duration_seconds`,
  `process_cpu_seconds_total`, `process_resident_memory_bytes`.
- ML (custom) : `ml_model_r2_score`, `ml_model_mae`, `ml_model_accuracy`,
  `ml_predictions_total` (compteur par catégorie de risque).

**Module Monitoring Streamlit** : affiche les métriques depuis `metadata.json`
(performance modèle) et interroge l'endpoint `/metrics` Prometheus (infra).

---

## 10. Décisions Transversales

| Décision | Valeur retenue | Raison |
|----------|---------------|--------|
| Langue du code | Noms de fichiers en anglais, commentaires/docstrings en français | PEP8 + convention constitution |
| Langue BDD | Noms de tables et colonnes en français | Constitution §2 |
| Versioning modèles | `v{YYYYMMDD}-{hash_court}` dans metadata.json | Traçabilité soutenance |
| Port API | 8000 | Convention FastAPI |
| Port Streamlit | 8501 | Convention Streamlit |
| Port Grafana | 3000 | Convention Grafana |
| Port Prometheus | 9090 | Convention Prometheus |
| Seed aléatoire | 42 | Reproductibilité (constitution Principe I) |
