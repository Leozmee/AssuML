# Implementation Plan: ETL Pipeline 3 Sources

**Branch**: `006-etl-pipeline` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)

## Summary

Implémentation d'un pipeline ETL Python standalone couvrant 2 sources externes (API OpenWeatherMap + scraping santemagazine.fr) qui viennent compléter le CSV Kaggle déjà chargé (Feature 005). Les données sont transformées et insérées dans les tables `donnees_meteo` et `articles` de PostgreSQL via SQLAlchemy ORM. Un fichier `database/queries.sql` documente 10+ requêtes SQL complexes pour démontrer les compétences C4 et C5.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: requests 2.31+, beautifulsoup4 4.12+, sqlalchemy 2.0+ (déjà installé), pandas 2.0+, python-dotenv (déjà installé)
**Storage**: PostgreSQL 15+ local (`assuml_db`) + fichiers JSON locaux (`data/external/`)
**Testing**: pytest — tests unitaires sur les fonctions de transformation (SQLite in-memory pour les insertions), mock requests pour l'API
**Target Platform**: scripts locaux standalone, exécutables via `python -m data_pipeline.extract.*`
**Project Type**: pipeline ETL batch (pas de serveur, pas d'interface)
**Performance Goals**: collecte des 4 régions météo < 30s, scraping 5+ articles < 60s
**Constraints**: free tier OpenWeatherMap (1 000 req/jour), pas de credentials dans le code, idempotence obligatoire
**Scale/Scope**: 4 appels API/exécution, ~10-20 articles/exécution de scraping

## Constitution Check

| Principe | Statut | Notes |
|---|---|---|
| I — 3 sources de données | ✅ PASS | CSV (Feature 005), API météo (cette feature), scraping (cette feature) |
| II — ML rigoureux | ✅ N/A | Pas de ML dans cette feature |
| III — Séparation des couches | ✅ PASS | Pipeline ETL standalone, n'appelle pas FastAPI ni Streamlit |
| IV — RGPD et sécurité | ✅ PASS | OPENWEATHER_API_KEY dans `.env`, pas de PII dans les données météo/articles |
| V — Qualité et testabilité | ✅ PASS | Tests pytest obligatoires, docstrings français, flake8 |

**Résultat** : Aucune violation. Implémentation autorisée.

## Project Structure

### Documentation (cette feature)

```text
specs/006-etl-pipeline/
├── plan.md          # Ce fichier
├── research.md      # Décisions techniques
├── data-model.md    # Entités et flux
├── quickstart.md    # Scénarios de test
└── tasks.md         # Généré par /speckit-tasks
```

### Source Code

```text
data_pipeline/
├── __init__.py
├── extract/
│   ├── __init__.py
│   ├── api_extractor.py        # US1 — OpenWeatherMap → backup JSON → donnees_meteo
│   └── scraper.py              # US2 — santemagazine.fr → backup JSON → articles
├── transform/
│   ├── __init__.py
│   ├── transform_meteo.py      # Extraction champs, calcul saison
│   └── transform_articles.py   # Nettoyage HTML, normalisation dates, déduplication
└── load/
    ├── __init__.py
    └── db_loader.py            # insert_donnees_meteo(), insert_articles()

database/
└── queries.sql                 # US3 — 10+ requêtes SQL complexes documentées

data/external/
├── api_data/                   # Backup JSON météo (horodaté, .gitignore)
└── scraped_data/               # Backup JSON articles (horodaté, .gitignore)

tests/unit/
├── test_transform_meteo.py     # Tests fonctions de transformation météo
├── test_transform_articles.py  # Tests nettoyage HTML, normalisation dates
└── test_db_loader.py           # Tests insertions (SQLite in-memory)
```

**Structure Decision** : Pipeline ETL standalone en 3 couches (extract / transform / load), cohérent avec le pattern déjà utilisé en Feature 005. Pas de nouveau projet, extension des répertoires existants.

## Decisions techniques clés

### API météo
- Endpoint : `GET /data/2.5/weather?q={city}&appid={key}&units=metric`
- Villes : Phoenix (southwest), Atlanta (southeast), Seattle (northwest), Boston (northeast)
- Champs extraits : `main.temp`, `main.humidity`, `rain.1h` (0.0 si absent)
- Saison : calculée depuis `datetime.now().month` avec mapping mois → saison

### Scraping
- Site : `https://www.santemagazine.fr/actualites`
- Bibliothèques : requests (timeout=10s) + BeautifulSoup4 (html.parser)
- Extraction : balises `article`, `h2`/`h3` pour titre, `a[href]` pour URL, `p` pour résumé, `time` ou méta `article:published_time` pour date
- Gestion erreurs : `try/except requests.exceptions.RequestException` → log + liste vide

### Loader
- ORM SQLAlchemy : `DonneesMeteo` et `Article` depuis `database/models.py`
- Articles : `insert(Article).on_conflict_do_nothing(index_elements=['url_source'])`
- Météo : insertion simple (pas de contrainte UNIQUE, historisation souhaitée)

### Backup JSON
- Format : `data/external/api_data/meteo_{YYYYMMDD_HHMMSS}.json`
- Format : `data/external/scraped_data/articles_{YYYYMMDD_HHMMSS}.json`
- Créé AVANT toute insertion en base

### Requêtes SQL (queries.sql)
10 requêtes documentées :
1. Jointure clients × regions
2. COUNT clients par région
3. IMC moyen par région
4. Régions avec >100 fumeurs (HAVING)
5. Coût prédit moyen par catégorie (clients × predictions)
6. Clients sans prédiction (LEFT JOIN IS NULL)
7. Top 3 clients par coût prédit (sous-requête RANK)
8. Distribution fumeurs par région (GROUP BY multi-colonnes)
9. Clients avec contrats actifs — 3 tables (clients × regions × contrats)
10. Tableau de bord par région — multi-agrégations (COUNT, AVG, %)
