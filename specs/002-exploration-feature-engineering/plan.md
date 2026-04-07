# Implementation Plan: Exploration des Données et Feature Engineering

**Branch**: `002-exploration-feature-engineering` | **Date**: 2026-04-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-exploration-feature-engineering/spec.md`

## Summary

Créer deux notebooks Jupyter documentés (exploration EDA + feature engineering)
et deux scripts Python réutilisables (`cleaning.py`, `normalization.py`) à partir
du dataset `insurance.csv` (1 338 lignes). La feature produit les données préparées
(`data/processed/features.csv`) nécessaires à l'entraînement des modèles ML de
la feature 001.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: Pandas 2.0+, NumPy, Matplotlib, Seaborn, Plotly Express,
  scikit-learn 1.4+ (train_test_split, pd.get_dummies), Jupyter / nbformat
**Storage**: Fichiers CSV locaux (`data/small_data/insurance.csv` → `data/processed/features.csv`)
**Testing**: pytest (tests unitaires sur cleaning.py et normalization.py)
**Target Platform**: Local — Jupyter Notebook / JupyterLab
**Project Type**: Data science / notebook
**Performance Goals**: Exécution notebook < 2 min, génération features.csv < 10 s
**Constraints**: Dataset fixe (1 338 lignes), encodage one-hot avec drop_first=True
  (northeast référence), random_state=42, nommage colonnes en français
**Scale/Scope**: 1 338 lignes, 7 colonnes brutes → ≈ 10 colonnes encodées

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Gate | Statut | Justification |
|----------|------|--------|---------------|
| I. Trois Sources | N/A pour cette feature | ✅ | Feature de preprocessing — la source CSV est la source 1 définie dans la constitution |
| II. ML Rigoureux | train_test_split ≥ 70/30 requis | ✅ | Split 80/20 avec random_state=42 |
| III. Séparation des Couches | N/A (pas de BDD ni API dans cette feature) | ✅ | Notebooks et scripts purement locaux |
| IV. RGPD & Sécurité | Pas de PII dans insurance.csv | ✅ | Dataset anonymisé |
| V. Qualité & Testabilité | PEP8, docstrings français, 1 fichier = 1 responsabilité | ✅ | cleaning.py et normalization.py séparés, docstrings requis |

**Constitution Check Post-Design** : ✅ Tous les gates passent.

## Project Structure

### Documentation (this feature)

```text
specs/002-exploration-feature-engineering/
├── plan.md          # Ce fichier
├── research.md      # Décisions de visualisation et encodage
├── data-model.md    # Structure des datasets (brut → préparé)
├── quickstart.md    # Guide d'exécution des notebooks
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
notebooks/
├── 01_data_exploration.ipynb      # EDA : chargement, stats, 8+ visualisations, insights
└── 02_feature_engineering.ipynb  # Encodage, target, split, sauvegarde features.csv

data/
├── small_data/
│   └── insurance.csv              # Source (existante, 1 338 lignes)
└── processed/
    └── features.csv               # Sortie : dataset encodé + categorie_risque

data_pipeline/
└── transform/
    ├── cleaning.py                # rename_columns(df) : anglais → français
    └── normalization.py           # encode_categoricals(df) : encodage numérique

tests/
└── unit/
    ├── test_cleaning.py           # Tests rename_columns()
    └── test_normalization.py      # Tests encode_categoricals()
```

**Structure Decision**: Notebooks dans `notebooks/`, scripts réutilisables dans
`data_pipeline/transform/` (cohérent avec la structure définie dans la feature 001),
données préparées dans `data/processed/` (nouveau sous-répertoire à créer).

## Complexity Tracking

> Aucune violation de constitution — section non applicable.
