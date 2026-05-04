# Implementation Plan: Modèle de Régression — Prédiction du Coût Médical

**Branch**: `003-regression-model` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-regression-model/spec.md`

---

## Summary

Entraîner, comparer et optimiser un modèle de régression pour prédire le coût médical annuel (`charges`) à partir du dataset assuré. Trois algorithmes sont comparés (LinearRegression, RandomForestRegressor, GradientBoostingRegressor) avec métriques R², MAE, RMSE. Le meilleur est optimisé via GridSearchCV et validé en cross-validation 5 plis (objectif R² > 0.80). Le résultat final est un Pipeline scikit-learn complet (ColumnTransformer + modèle) sérialisé dans `regression.pkl`, utilisable via la fonction `predict_cost()` qui accepte les paramètres bruts d'un assuré.

**Données d'entrée** : `data/processed/features.csv` (1 338 lignes, produit par la feature 002).
**Livrables** : `notebooks/03_model_training.ipynb`, `ml_models/training/train_regression.py`, `ml_models/saved_models/regression.pkl`, `ml_models/prediction/predict.py`.

---

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: scikit-learn 1.4+, pandas 2.0+, numpy, joblib, matplotlib, seaborn
**Storage**: fichiers CSV (entrée) + fichier `.pkl` (sortie sérialisée) — pas de base de données dans cette feature
**Testing**: pytest (`tests/unit/test_regression.py`)
**Target Platform**: environnement Python local / CI GitHub Actions
**Project Type**: script ML standalone + notebook d'exploration
**Performance Goals**: R² > 0.80 sur le test set (20%) et sur la cross-validation 5 plis
**Constraints**: random_state=42 sur tous les appels stochastiques ; preprocessing `fit` uniquement sur X_train ; `regression.pkl` non commité
**Scale/Scope**: 1 338 lignes, 8 features d'entrée, 1 target continue (`charges`)

### Décision design — Pipeline et predict_cost()

**Problème** : `features.csv` contient déjà `region` encodée en 3 colonnes one-hot (`region_northwest`, `region_southeast`, `region_southwest`), mais `predict_cost()` doit accepter `region` comme string (`"northeast"`, `"southwest"`, etc.) pour être utilisable par la feature 001 (API FastAPI) avec des paramètres client bruts.

**Solution retenue** :
1. **Notebook (US1/US2)** : lit `features.csv` tel quel (8 colonnes déjà encodées). Le ColumnTransformer applique StandardScaler sur `[age, imc, enfants]` et passthrough sur `[sexe, fumeur, region_northwest, region_southeast, region_southwest]`.
2. **Script standalone (US3)** : lit `features.csv` mais construit le Pipeline de façon identique. Le `.pkl` sérialisé attend donc un DataFrame avec les 8 colonnes encodées.
3. **`predict_cost()` (US4)** : reçoit les paramètres bruts (dont `region: str`), construit en interne le DataFrame 8-colonnes (conversion region → one-hot, sexe/fumeur déjà 0/1), puis appelle `pipeline.predict()`.

Cette approche garantit que le pipeline lui-même est stateless vis-à-vis du format brut, et que toute la logique de conversion brut→features est centralisée dans `predict_cost()`.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Exigence constitution | Statut cette feature |
|----------|----------------------|----------------------|
| **I — 3 Sources** | CSV = source d'entraînement ML unique | ✅ `features.csv` dérivé de `insurance.csv` (Kaggle CSV). Pas d'API ni scraping dans cette feature — conforme (sources gérées par la feature 001 ETL). |
| **II — ML Rigoureux** | Régression sur `charges`, 3 algos comparés, R²/MAE/RMSE, split ≥ 70/30, fit uniquement sur train, metadata.json | ✅ 3 algos comparés, split 80/20, random_state=42. ⚠️ `metadata.json` à créer dans le script (voir FR-012 étendu). |
| **III — Séparation couches** | ML dans `ml_models/`, logique métier dans `business/` | ✅ predict_cost() dans `ml_models/prediction/predict.py` uniquement. La décision (accepter/refuser) reste dans `business/risk_engine.py` (feature 001). |
| **IV — RGPD & Sécurité** | `.pkl` dans `.gitignore`, pas de credentials hardcodés | ✅ `.gitignore` existant exclut `*.pkl`. Pas de credentials dans cette feature. |
| **V — Qualité** | PEP8, docstrings français, 1 test pytest minimum | ✅ À vérifier à l'implémentation. Test `tests/unit/test_regression.py` requis. |

**Violation identifiée (Principe II)** : `metadata.json` non mentionné dans la spec originale → **ajouté au plan** comme tâche obligatoire dans le script standalone (non bloquant pour la spec, conforme à la constitution).

**Constitution Check : PASS** (avec extension metadata.json).

---

## Project Structure

### Documentation (this feature)

```text
specs/003-regression-model/
├── plan.md              # Ce fichier
├── research.md          # Décisions techniques (Phase 0)
├── data-model.md        # Entités et flux de données (Phase 1)
├── quickstart.md        # Commandes pour reproduire (Phase 1)
├── checklists/
│   └── requirements.md  # Checklist qualité spec
└── tasks.md             # Liste de tâches (produit par /speckit-tasks)
```

### Source Code (repository root)

```text
notebooks/
└── 03_model_training.ipynb   # Exploration, comparaison, optimisation, visualisations

ml_models/
├── __init__.py
├── training/
│   ├── __init__.py
│   └── train_regression.py   # Script standalone (python -m ml_models.training.train_regression)
├── prediction/
│   ├── __init__.py
│   └── predict.py            # predict_cost() — interface production
└── saved_models/
    ├── regression.pkl         # Pipeline sérialisé (gitignored)
    └── metadata.json          # Métriques + hyperparamètres + date (commité)

tests/
└── unit/
    └── test_regression.py    # Tests predict_cost() et pipeline
```

**Structure Decision** : structure `ml_models/` existante dans le projet (définie par la constitution §III et le CLAUDE.md). Cette feature ajoute `03_model_training.ipynb`, `train_regression.py`, `predict.py` et `metadata.json`. Les `__init__.py` sont créés si absents.

---

## Complexity Tracking

Aucune violation de constitution non justifiée dans ce plan.

| Extension | Justification |
|-----------|---------------|
| `metadata.json` ajouté (absent de la spec) | Requis par la constitution Principe II pour la traçabilité ML (version, date, scores, hyperparamètres). Indispensable pour le module Monitoring (feature 001 US8). |
