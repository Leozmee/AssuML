# Implementation Plan: Base de Données PostgreSQL — Schéma & Couche d'Accès

**Branch**: `005-postgres-db-setup` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-postgres-db-setup/spec.md`

---

## Summary

Créer le socle de données PostgreSQL d'AssuML : exécuter `database/schema.sql` (7 tables,
22 contraintes CHECK, 21 index, soft delete, 5 FK CASCADE), exposer une couche d'accès Python
via SQLAlchemy 2.0 (`connection.py`, `models.py`, `crud.py`), et charger les 1338 lignes de
`insurance.csv` dans `clients` via `database/load_csv.py`. Le tout est orchestré par
`scripts/setup_db.py`. Les credentials sont dans `.env` (jamais commités).

**Données** : `data/small_data/insurance.csv` → table `clients`.
Modules existants réutilisés : `data_pipeline/transform/cleaning.py` (rename_columns uniquement).

---

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: SQLAlchemy 2.0+, psycopg2-binary, python-dotenv, pandas
**Storage**: PostgreSQL 15+ local (Homebrew) — base `assuml_db`, user `assuml_user`
**Testing**: pytest — `tests/integration/test_db_connection.py`, `tests/unit/test_crud.py`
**Target Platform**: macOS (développement local), Linux (CI GitHub Actions)
**Project Type**: couche de persistance + scripts d'initialisation
**Performance Goals**: chargement 1338 lignes < 30s, lecture client par id < 100ms
**Constraints**: soft delete obligatoire (constitution Principe IV), pas de credentials hardcodés,
nommage français pour tables/colonnes, `schema.sql` idempotent (DROP IF EXISTS)
**Scale/Scope**: 7 tables, 1338 lignes initiales, 9 fonctions CRUD, 1 script setup

### Décisions design clés

**Réutilisation partielle** : `rename_columns()` de `cleaning.py` pour le renommage de colonnes.
`encode_categoricals()` de `normalization.py` NON utilisé (encodage ML incompatible avec la BDD).

**Mapping CSV→BDD** : sex→'homme'/'femme' (VARCHAR, pas int), smoker→bool, region→region_id FK,
charges ignoré (non stocké dans `clients`), email/téléphone→NULL.

**Pattern CRUD** : pas de schemas Pydantic dans cette feature (ils vivent dans `api/schemas/`).
Les fonctions CRUD acceptent des paramètres scalaires + retournent les objets ORM directement.

**Idempotence setup_db.py** : DROP TABLE IF EXISTS CASCADE dans schema.sql → rejouable à zéro.

---

## Constitution Check

| Principe | Exigence | Statut |
|----------|----------|--------|
| **I — 3 Sources** | CSV chargé dans `clients` ; tables `donnees_meteo` et `articles` créées pour API/ETL | ✅ Tables créées, CSV chargé |
| **II — ML Rigoureux** | Pas de modèle ML dans cette feature | ✅ N/A |
| **III — Séparation couches** | `database/` = couche persistance uniquement ; pas d'accès direct depuis Streamlit | ✅ Conforme |
| **IV — RGPD & Sécurité** | Soft delete via `date_suppression`, email/tel nullable, pas de credentials dans le code, `.env` gitignored | ✅ Conforme |
| **V — Qualité** | PEP8, docstrings français, tests pytest, flake8+black | ✅ Prévu |

**Constitution Check : PASS**

---

## Project Structure

### Documentation (this feature)

```text
specs/005-postgres-db-setup/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
database/
├── __init__.py
├── schema.sql          # DDL complet (7 tables, 22 CHECK, 21 index)
├── connection.py       # engine, SessionLocal, get_db()
├── models.py           # 7 modèles ORM SQLAlchemy 2.0
├── crud.py             # 9 fonctions CRUD
└── load_csv.py         # Chargement insurance.csv → clients

scripts/
└── setup_db.py         # Script d'initialisation complet

tests/
├── unit/
│   └── test_crud.py    # Tests CRUD avec base SQLite en mémoire
└── integration/
    └── test_db_connection.py  # Tests connexion PostgreSQL réelle

.env.example            # Template variables d'environnement (commité)
.env                    # Credentials réels (gitignored — déjà présent)
```

**Structure Decision** : `database/` est le répertoire dédié à la couche persistance,
conforme à la constitution Principe III. `scripts/` centralise les outils opérationnels.
Les tests sont séparés unitaires (SQLite in-memory, pas de dépendance PostgreSQL) et
intégration (PostgreSQL réel, marqués `@pytest.mark.integration`).

---

## Complexity Tracking

Aucune violation de constitution. Aucune complexité non justifiée.
