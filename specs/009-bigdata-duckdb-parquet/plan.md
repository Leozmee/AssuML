# Implementation Plan: Big Data — DuckDB + Parquet 5M lignes

**Branch**: `009-bigdata-duckdb-parquet` | **Date**: 2026-06-01 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/009-bigdata-duckdb-parquet/spec.md`

## Summary

Générer un fichier Parquet de 5 millions de lignes synthétiques à partir du CSV source,
exposer 9 requêtes analytiques via une classe `DuckDBAnalytics` (DuckDB in-memory en
lecture directe sur Parquet), et remplacer le placeholder Analytics dans Streamlit
par un tableau de bord complet avec 6 sections de visualisation Plotly.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: NumPy, Pandas 2.0+, PyArrow, DuckDB, Plotly Express, Streamlit 1.32+  
**Storage**: Parquet (lecture seule) — PAS de PostgreSQL pour cette feature  
**Testing**: pytest (tests unitaires `DuckDBAnalytics`, test de schéma Parquet)  
**Target Platform**: macOS/Linux local — script one-shot + module importé par Streamlit  
**Project Type**: Script de génération de données + module analytique + page Streamlit  
**Performance Goals**: génération < 2 minutes sur 5M lignes ; chaque requête DuckDB < 5 secondes  
**Constraints**: Parquet gitignored ; DuckDB en lecture seule ; accès direct sans API FastAPI  
**Scale/Scope**: 5 000 000 lignes × 11 colonnes (~150-200 Mo Parquet)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Status | Justification |
| -------- | ------ | ------------- |
| I — Trois sources de données | ✅ | CSV source utilisé pour générer les données synthétiques ; Big Data sert uniquement l'Analytics (pas l'entraînement ML) |
| II — ML rigoureux et traçable | ✅ | Les modèles ML NE SONT PAS réentraînés sur le Parquet synthétique |
| III — Séparation stricte des couches | ✅ | Exception DuckDB explicitement documentée dans la constitution : "le module Analytics lit DuckDB directement (lecture seule Parquet) pour les performances" |
| IV — RGPD et sécurité | ✅ | `data/big_data/` ajouté au `.gitignore` ; pas de PII dans le dataset synthétique ; pas de credentials |
| V — Qualité, testabilité, documentation | ✅ | Docstrings et commentaires en français ; pytest requis pour `DuckDBAnalytics` et le schéma Parquet |

**Aucune violation — feu vert pour l'implémentation.**

## Project Structure

### Documentation (this feature)

```text
specs/009-bigdata-duckdb-parquet/
├── plan.md              ← ce fichier
├── research.md          ← Phase 0 (décisions techniques)
├── data-model.md        ← Phase 1 (schéma Parquet)
├── checklists/
│   └── requirements.md  ← créé par /speckit-specify
└── tasks.md             ← Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
big_data/
├── __init__.py
├── generate_synthetic.py     # Script one-shot de génération
└── duckdb_analytics.py       # Classe DuckDBAnalytics

data/big_data/
└── insurance_big.parquet     # 5M lignes (~150-200 Mo) — gitignored

streamlit_app/pages/
└── 2_📊_Analytics.py         # Réécrit (remplace placeholder Feature 7)

tests/unit/
└── test_duckdb_analytics.py  # Tests des 9 méthodes + schéma
```

**Structure Decision**: Module `big_data/` à la racine du projet (cohérent avec
`ml_models/`, `data_pipeline/`, `business/` — chaque domaine a son propre dossier).
