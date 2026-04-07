<!--
SYNC IMPACT REPORT
==================
Version change: (template non rempli) → 1.0.0
Bump rationale: MINOR — première ratification, remplissage complet de tous les
  placeholders à partir de la constitution fournie par le développeur.

Principes modifiés: N/A (première version)
Sections ajoutées: Toutes (première version)
Sections supprimées: Aucune

Templates examinés:
  ✅ .specify/templates/plan-template.md — Constitution Check aligné avec les
      principes I–V ci-dessous.
  ✅ .specify/templates/spec-template.md — Format User Stories compatible;
      aucune contrainte supplémentaire requise.
  ✅ .specify/templates/tasks-template.md — Catégories de tâches compatibles;
      aucun nouveau type de tâche requis par la constitution.
  ✅ .specify/templates/agent-file-template.md — Pas de références aux
      principes; aucune mise à jour requise.
  ⚠  Pas de répertoire commands/ trouvé sous .specify/templates — ignoré.

TODOs différés: Aucun — tous les placeholders résolus.
-->

# AssuML Constitution

## Principes fondamentaux

### I. Trois Sources de Données Obligatoires

Toute phase d'ingestion de données DOIT intégrer exactement trois sources
distinctes conformément à la compétence C1 :

- **CSV** : `data/small_data/insurance.csv` (Kaggle Medical Cost Personal
  Dataset, 1 338 lignes) — source d'entraînement ML unique.
- **API REST** : OpenWeatherMap (gratuit) — météo par région, stockée dans
  la table `donnees_meteo` et sous `data/external/api_data/` via
  `data_pipeline/extract/api_extractor.py`.
- **Web Scraping** : BeautifulSoup + Requests — articles assurance/santé,
  stockés dans la table `articles` et sous `data/external/scraped_data/`
  via `data_pipeline/extract/scraper.py`. PAS de n8n — tout est codé Python.

Les modèles ML sont entraînés UNIQUEMENT sur `insurance.csv`. Le Big Data
(10 M lignes Parquet) est utilisé exclusivement pour la compétence C2
(Analytics) et ne sert JAMAIS à l'entraînement.

**Rationale** : Les 21 compétences Simplon exigent la démonstration explicite
de sources hétérogènes. Le mélange de sources valide les compétences C1, C2,
C5 et C9 de façon traçable.

### II. Machine Learning Rigoureux et Traçable

Deux modèles DOIVENT être entraînés, évalués et sauvegardés :

- **Régression** (`ml_models/saved_models/regression.pkl`) : prédit `charges`
  (coût médical annuel, variable continue). Algorithmes à comparer :
  `RandomForestRegressor`, `LinearRegression`, `GradientBoostingRegressor`.
  Métriques obligatoires : R², MAE, RMSE.
- **Classification** (`ml_models/saved_models/classification.pkl`) : prédit
  `categorie_risque` construite depuis `charges` :
  `< 5 000 → faible`, `5 000–15 000 → moyen`, `15 000–30 000 → eleve`,
  `> 30 000 → critique`. Algorithmes : `RandomForestClassifier`,
  `GradientBoostingClassifier`. Métriques : accuracy, precision, recall,
  f1-score, matrice de confusion.

Toute expérimentation DOIT utiliser un train/test split ≥ 70/30. Les étapes
de preprocessing (scaling, encodage) DOIVENT être ajustées (`fit`) uniquement
sur les données d'entraînement. Les métadonnées (version, date, scores,
hyperparamètres) DOIVENT être enregistrées dans
`ml_models/saved_models/metadata.json`.

La logique métier post-modèle (scoring et décision) vit dans
`business/scoring.py` et `business/risk_engine.py` :
`faible/moyen → accepter`, `eleve → examiner`, `critique → refuser`.

**Rationale** : La traçabilité complète de l'expérimentation (algorithmes
comparés, métriques, version) est requise pour la validation de la compétence
C9 et pour la reproductibilité des résultats lors de la soutenance.

### III. Séparation Stricte des Couches Applicatives

L'architecture trois-tiers DOIT être respectée sans exception :

- **Streamlit** est le seul frontend. PAS de Django, PAS de HTML/CSS manuel.
  Streamlit appelle TOUJOURS l'API FastAPI pour les données PostgreSQL.
  **Exception unique** : le module Analytics lit DuckDB directement (lecture
  seule Parquet) pour les performances sur 10 M lignes.
- **FastAPI** est la seule porte d'entrée vers PostgreSQL. Tout accès aux
  données relationnelles depuis Streamlit passe par les endpoints définis
  en §7 de ce document.
- **DuckDB** opère en lecture seule sur les fichiers Parquet. Il ne modifie
  JAMAIS PostgreSQL et n'est utilisé que par le module Analytics Streamlit.
- **PostgreSQL** contient 7 tables uniquement (voir §3). Pas de tables de
  logs ou monitoring dans la base — ces fonctions sont déléguées à
  Prometheus + Grafana.

**Rationale** : La séparation claire des couches garantit la maintenabilité,
facilite les tests unitaires par couche, et correspond aux patterns attendus
en production pour un système IA certifié.

### IV. Conformité RGPD et Sécurité des Données

Les règles suivantes sont NON NÉGOCIABLES :

- **Soft delete** : jamais de `DELETE` physique sur `clients`. La suppression
  DOIT utiliser `date_suppression` (nullable, indexé partiellement sur les
  clients actifs).
- **PII nullable** : `email` et `telephone` DOIVENT rester nullable (collecte
  optionnelle, conformité RGPD).
- **Pas de credentials hardcodés** : toutes les clés d'API et chaînes de
  connexion DOIVENT être lues depuis `.env` (jamais commitées).
- **Fichiers binaires exclus** : `.pkl` et `.parquet` DOIVENT être dans
  `.gitignore` et ne JAMAIS être commités.
- **Nommage en français** : les noms de tables, colonnes et variables métier
  DOIVENT être en français. Les noms de fichiers Python restent en anglais
  (convention PEP 8). Pas de mélange dans un même contexte.

**Rationale** : La conformité RGPD est évaluée comme compétence distincte.
Les données personnelles (email, téléphone) étant optionnelles, leur
nullabilité évite toute obligation de collecte non justifiée.

### V. Qualité, Testabilité et Documentation

- Chaque fichier Python DOIT avoir une responsabilité unique
  (principe de responsabilité unique).
- Le code DOIT respecter PEP 8 (vérifié par `flake8` + `black`).
- Toutes les fonctions DOIVENT avoir des docstrings en français.
- Les commentaires inline DOIVENT être en français.
- Les messages de commit DOIVENT être en français.
- Toute fonctionnalité livrée DOIT être couverte par au moins un test
  `pytest`.
- Les tests DOIVENT être organisés par couche : `tests/unit/`,
  `tests/integration/`, `tests/contract/`.

**Rationale** : La certification Simplon évalue 21 compétences, dont la
qualité du code et la capacité à documenter et tester. Un code non testé
ou non documenté ne peut pas être défendu en soutenance.

## Normes de Données et Stack Technique

**Stack obligatoire** (toute déviation DOIT être justifiée dans le plan) :

| Couche | Technologie |
|--------|-------------|
| Backend API | FastAPI + Pydantic + SQLAlchemy ORM |
| Frontend | Streamlit |
| BDD relationnelle | PostgreSQL 15+ |
| Big Data | DuckDB + Parquet (lecture seule) |
| ML | scikit-learn + Pandas + NumPy + Joblib |
| Visualisations | Plotly Express |
| Scraping | BeautifulSoup + Requests |
| Tests | pytest |
| Linting | flake8 + black |
| CI/CD | GitHub Actions + Docker |
| Monitoring | Prometheus + Grafana |
| Versioning | Git + GitHub |

**Schéma PostgreSQL — 7 tables** :
- `regions` (référentiel, pré-remplie : southwest, southeast, northwest, northeast)
- `clients`, `predictions`, `contrats`, `sinistres` (tables métier)
- `donnees_meteo`, `articles` (sources externes)
- 5 FK avec `ON DELETE CASCADE`, 22 contraintes `CHECK`, 20 index,
  soft delete via `date_suppression`.

**Big Data** : `data/big_data/insurance_big.parquet` (10 M lignes
synthétiques générées depuis `insurance.csv`). Colonnes : `age`, `sex`,
`bmi`, `children`, `smoker`, `region`, `charges`, `charges_log`,
`age_group`, `bmi_category`, `risk_score`. Pas de MCD/MLD pour ce fichier
(table plate, usage lecture seule).

## Workflow et Planning

**Planning 8 semaines** :
- S1–S2 : Exploration des données + Machine Learning
- S3–S4 : BDD PostgreSQL + Pipeline ETL + 3 sources
- S5–S6 : API FastAPI + Streamlit (5 modules)
- S7 : CI/CD + Monitoring (GitHub Actions, Prometheus, Grafana)
- S8 : Documentation + Tests finaux + Soutenance

**Modules Streamlit** (5 modules obligatoires) :
1. Scoring — prédiction ML d'un client via API
2. Analytics — graphiques Plotly sur Big Data DuckDB (direct, pas via API)
3. CRUD — gestion clients via API
4. Monitoring ML — métriques et drift detection
5. Actualités — articles scrappés via API

**Endpoints FastAPI** (liste exhaustive définie, tout ajout DOIT être
documenté dans le spec de la feature concernée) :
- CRUD clients, liste prédictions/contrats/sinistres/articles/météo/KPIs
- POST `/api/predict/cout`, `/api/predict/risque`, `/api/predict/complet`
- Documentation Swagger accessible sur `/docs`

## Gouvernance

Cette constitution est le document de référence IMMUABLE du projet AssuML.
Elle supplante toute pratique informelle antérieure.

**Procédure d'amendement** : tout changement DOIT incrémenter la version
selon les règles sémantiques (MAJOR : suppression/redéfinition de principe ;
MINOR : ajout de principe ou section ; PATCH : clarification ou correction).
`LAST_AMENDED_DATE` DOIT être mis à jour à la date du changement.

**Revue de conformité** : chaque plan produit par les commandes speckit DOIT
inclure une section Constitution Check vérifiant l'alignement avec les
Principes I–V avant le début de l'implémentation.

**Contexte développeur** : Leo — background SAS, Snowflake, Power BI,
Python/Pandas, SQL. Les explications techniques DOIVENT tenir compte de
cette expertise et utiliser des analogies avec ces outils quand pertinent.

**Fichier de guidance runtime** : `.specify/templates/agent-file-template.md`
pour le contexte de développement actif (technologies, structure, changements
récents).

**Version**: 1.0.0 | **Ratifiée**: 2026-04-07 | **Dernière modification**: 2026-04-07
