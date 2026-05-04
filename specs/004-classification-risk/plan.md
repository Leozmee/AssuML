# Implementation Plan: Modèle de Classification — Niveau de Risque Assuré

**Branch**: `004-classification-risk` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-classification-risk/spec.md`

---

## Summary

Entraîner et comparer deux classificateurs (RandomForestClassifier, GradientBoostingClassifier) pour prédire la catégorie de risque d'un assuré (faible/moyen/eleve/critique). Le meilleur modèle est optimisé via GridSearchCV, validé en cross-validation 5 plis (objectif accuracy > 0.85), évalué avec matrice de confusion heatmap et courbes ROC one-vs-rest. Le résultat est un Pipeline sklearn sérialisé dans `classification.pkl`, `metadata.json` mis à jour avec les deux modèles, `predict_risk()` ajoutée dans `predict.py`, et les modules métier `business/scoring.py` + `business/risk_engine.py` créés. Un notebook `04_model_evaluation.ipynb` produit l'évaluation comparative régression vs classification.

**Données** : `data/processed/features.csv` (1 338 lignes). `regression.pkl` et `metadata.json` v1.0.0 déjà présents (feature 003).

---

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: scikit-learn 1.4+, pandas 2.0+, numpy, joblib, matplotlib, seaborn
**Storage**: fichiers CSV (entrée) + `.pkl` (sortie) + `metadata.json` (traçabilité) — pas de BDD dans cette feature
**Testing**: pytest (`tests/unit/test_classification.py`, `tests/unit/test_business.py`)
**Target Platform**: environnement Python local / CI GitHub Actions
**Project Type**: scripts ML standalone + notebooks d'exploration + modules métier Python purs
**Performance Goals**: accuracy > 0.85 sur le test set et sur la cross-validation 5 plis
**Constraints**: random_state=42 sur tous les appels stochastiques ; ColumnTransformer identique à la régression ; `classification.pkl` non commité ; fusion metadata.json (pas écrasement)
**Scale/Scope**: 1 338 lignes, 8 features, 4 classes cibles, 2 modules métier sans dépendance sklearn

### Décisions design clés

**Courbe ROC multiclasse** : `OneVsRestClassifier` + `label_binarize` + `roc_curve` par classe. Macro-average via `roc_auc_score(multiclass='ovr')`.

**Encodage de la target** : `categorie_risque` est une colonne string/Categorical dans features.csv. Le Pipeline sklearn gère les labels string nativement via les classificateurs d'ensemble. Pour les courbes ROC, `label_binarize` avec ordre fixe `['faible', 'moyen', 'eleve', 'critique']`.

**predict_risk()** : même REGION_MAPPING que `predict_cost()`. Retourne `(categorie_risque: str, score_risque: float)` où `score_risque = max(predict_proba())`.

**calculer_prime()** : reçoit `cout_predit` (float) et `categorie_risque` (str). Applique le coefficient correspondant. Ne dépend pas de sklearn.

**metadata.json fusion** : `train_classification.py` lit le fichier existant (v1.0.0), ajoute la section `classification`, incrémente la version à `1.1.0`, et réécrit le fichier.

---

## Constitution Check

| Principe | Exigence | Statut |
|----------|----------|--------|
| **I — 3 Sources** | CSV = source ML unique | ✅ features.csv dérivé de insurance.csv |
| **II — ML Rigoureux** | Classification sur categorie_risque, 2 algos, accuracy/precision/recall/f1, matrice confusion, metadata.json | ✅ Tous couverts. metadata.json mis à jour avec les deux modèles. |
| **III — Séparation couches** | Logique ML dans `ml_models/`, logique métier dans `business/` | ✅ predict_risk() dans ml_models/prediction/, décision dans business/risk_engine.py |
| **IV — RGPD & Sécurité** | .pkl gitignored, pas de credentials | ✅ .gitignore existant couvre *.pkl |
| **V — Qualité** | PEP8, docstrings français, tests pytest | ✅ tests/unit/test_classification.py + test_business.py requis |

**Constitution Check : PASS**

---

## Project Structure

### Documentation (this feature)

```text
specs/004-classification-risk/
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
notebooks/
├── 03_model_training.ipynb     # Nouvelle section classification ajoutée
└── 04_model_evaluation.ipynb   # Nouveau — évaluation comparative

ml_models/
├── training/
│   └── train_classification.py  # Script standalone
├── prediction/
│   └── predict.py               # Ajout predict_risk()
└── saved_models/
    ├── classification.pkl        # Pipeline sérialisé (gitignored)
    └── metadata.json             # Mis à jour v1.1.0 (commité)

business/
├── __init__.py
├── scoring.py                   # calculer_prime()
└── risk_engine.py               # get_categorie_risque(), get_decision()

tests/unit/
├── test_classification.py       # Tests predict_risk()
└── test_business.py             # Tests scoring + risk_engine
```

**Structure Decision** : `business/` nouveau répertoire (prévu par la constitution et le CLAUDE.md). `ml_models/prediction/predict.py` étendu (pas recréé). `notebooks/03_model_training.ipynb` étendu avec la section classification.

---

## Complexity Tracking

| Extension | Justification |
|-----------|---------------|
| `notebooks/04_model_evaluation.ipynb` (nouveau notebook) | Requis par la spec US4 et la constitution (traçabilité ML, compétences C9/C11). Notebook dédié à l'évaluation comparative pour ne pas surcharger le notebook 03. |
| Section classification dans notebook 03 | Choix de cohérence : toutes les comparaisons d'algorithmes restent dans le même notebook d'entraînement. |
