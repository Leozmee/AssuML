# Research: Modèle de Régression — Prédiction du Coût Médical

**Feature**: `003-regression-model` | **Date**: 2026-05-04

---

## Décision 1 — Algorithme vainqueur attendu

**Décision** : GradientBoostingRegressor sera très probablement le meilleur algorithme sur ce dataset.

**Rationale** : Le dataset insurance.csv est bien documenté dans la littérature ML. GradientBoosting et RandomForest surpassent systématiquement LinearRegression sur ce dataset à cause des non-linéarités (interaction fumeur × IMC, clusters d'âge). Les benchmarks publics rapportent des R² de 0.85–0.90 pour GradientBoosting vs 0.75–0.78 pour LinearRegression.

**Alternatives considérées** :
- LinearRegression : R² attendu ≈ 0.75 (sous-capture les interactions non-linéaires)
- RandomForestRegressor : R² attendu ≈ 0.86 (performant mais légèrement inférieur à GBR)
- GradientBoostingRegressor : R² attendu ≈ 0.87–0.89 (retenu comme meilleur candidat)

---

## Décision 2 — Grille d'hyperparamètres GridSearchCV

**Décision** : Grille modérée pour rester sous 3 minutes d'entraînement.

```python
param_grid = {
    'model__n_estimators': [100, 200],
    'model__max_depth': [3, 4, 5],
    'model__min_samples_split': [2, 5],
    'model__min_samples_leaf': [1, 2],
}
# cv=5, scoring='r2', n_jobs=-1
# Nombre de combinaisons : 2 × 3 × 2 × 2 = 24 fits × 5 folds = 120 fits
```

**Rationale** : 120 fits sur 1 338 lignes s'exécutent en ~60–90 secondes avec n_jobs=-1. Couvre les 4 hyperparamètres obligatoires de la spec (FR-005) sans allonger excessivement le notebook.

**Alternatives considérées** :
- RandomizedSearchCV : plus rapide mais moins exhaustif — rejeté (grille petite, exhaustif préférable)
- Grille large (n_estimators jusqu'à 500) : temps excessif, gains marginaux

---

## Décision 3 — Architecture du ColumnTransformer

**Décision** : ColumnTransformer avec deux transformateurs + passthrough.

```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler

numeric_features = ['age', 'imc', 'enfants']
binary_features = ['sexe', 'fumeur',
                   'region_northwest', 'region_southeast', 'region_southwest']

preprocessor = ColumnTransformer([
    ('scaler', StandardScaler(), numeric_features),
    ('passthrough', 'passthrough', binary_features),
])
```

**Rationale** :
- `sexe` et `fumeur` sont déjà 0/1 dans features.csv → pas besoin d'encodage, StandardScaler inutile sur des binaires.
- `region_*` sont déjà one-hot → passthrough.
- StandardScaler sur `age`, `imc`, `enfants` améliore légèrement la convergence (surtout utile si on compare avec LinearRegression).

**Alternatives considérées** :
- StandardScaler sur toutes les colonnes : fausse les binaires (0/1 → [-1.2, 0.8]) — rejeté
- Pas de preprocessing : LinearRegression pénalisée — rejeté

---

## Décision 4 — Interface predict_cost() : conversion region

**Décision** : predict_cost() convertit la string `region` en 3 colonnes one-hot avant d'appeler le pipeline.

```python
REGION_MAPPING = {
    'northeast': {'region_northwest': 0, 'region_southeast': 0, 'region_southwest': 0},
    'northwest': {'region_northwest': 1, 'region_southeast': 0, 'region_southwest': 0},
    'southeast': {'region_northwest': 0, 'region_southeast': 1, 'region_southwest': 0},
    'southwest': {'region_northwest': 0, 'region_southeast': 0, 'region_southwest': 1},
}
```

**Rationale** : Le pipeline est entraîné sur les 8 colonnes de features.csv. predict_cost() expose une API propre pour la feature 001 (valeurs brutes client). La conversion est centralisée en un seul endroit, pas dans le pipeline (qui resterait compatible avec features.csv pour le re-entraînement).

**Alternatives considérées** :
- Pipeline avec OneHotEncoder natif sur `region` string : nécessiterait de lire insurance.csv (pas features.csv) dans le script d'entraînement → rupture avec la spec. Rejeté.
- Conversion dans l'API FastAPI (feature 001) : viole la SRP (l'API ne doit pas connaître le schéma interne du ML). Rejeté.

---

## Décision 5 — metadata.json

**Décision** : Créer `ml_models/saved_models/metadata.json` dans le script standalone.

```json
{
  "version": "1.0.0",
  "date_entrainement": "2026-05-04",
  "algorithme": "GradientBoostingRegressor",
  "hyperparametres": {"n_estimators": 200, "max_depth": 4, ...},
  "metriques_test": {"r2": 0.87, "mae": 2341.5, "rmse": 3120.8},
  "metriques_cv": {"r2_mean": 0.86, "r2_std": 0.02},
  "features": ["age", "sexe", "imc", "enfants", "fumeur",
               "region_northwest", "region_southeast", "region_southwest"],
  "target": "charges",
  "split": "80/20",
  "random_state": 42
}
```

**Rationale** : Requis par la constitution Principe II. Consommé par le module Monitoring Streamlit (feature 001, US8) pour afficher R²/MAE/RMSE en temps réel. Commité dans git (pas de données sensibles, pas de modèle binaire).

---

## Décision 6 — Module exécutable

**Décision** : `train_regression.py` avec bloc `if __name__ == '__main__'` ET compatible `python -m ml_models.training.train_regression`.

**Rationale** : `python -m` requiert que le package `ml_models` soit importable (PYTHONPATH ou installation). Les `__init__.py` dans `ml_models/` et `ml_models/training/` sont indispensables. La compatibilité `-m` permet l'exécution depuis la racine du projet sans manipulation du path.

---

## Résolution — NEEDS CLARIFICATION

Aucun marqueur [NEEDS CLARIFICATION] dans la spec. Tous les choix techniques ont été résolus par :
- Contraintes explicites de l'utilisateur (`/speckit-plan` args)
- Constitution AssuML (Principe II)
- Pratiques standard scikit-learn sur ce type de dataset
