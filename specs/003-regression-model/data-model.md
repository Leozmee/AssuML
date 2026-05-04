# Data Model: Modèle de Régression

**Feature**: `003-regression-model` | **Date**: 2026-05-04

---

## Entités et flux de données

### Entrée — Dataset d'entraînement

**Source** : `data/processed/features.csv` (produit par feature 002)

| Colonne | Type | Description | Valeurs |
|---------|------|-------------|---------|
| `age` | int | Âge de l'assuré | 18–64 |
| `sexe` | int | Sexe encodé | 0=homme, 1=femme |
| `imc` | float | Indice de masse corporelle | 15.96–53.13 |
| `enfants` | int | Nombre d'enfants à charge | 0–5 |
| `fumeur` | int | Statut fumeur encodé | 0=non, 1=oui |
| `region_northwest` | int | Région one-hot | 0 ou 1 |
| `region_southeast` | int | Région one-hot | 0 ou 1 |
| `region_southwest` | int | Région one-hot | 0 ou 1 |
| `charges` | float | **Target régression** — coût médical annuel USD | 1 121–63 770 |
| `categorie_risque` | str | Target classification (ignorée dans cette feature) | faible/moyen/eleve/critique |

**Dimensions** : 1 338 lignes × 10 colonnes. Features ML : 8 colonnes (sans `charges` et `categorie_risque`).

---

### Split train/test

| Split | Lignes | Usage |
|-------|--------|-------|
| X_train / y_train | ≈ 1 070 (80%) | Entraînement + fit du ColumnTransformer |
| X_test / y_test | ≈ 268 (20%) | Évaluation des métriques finales |

`random_state=42` sur tous les appels `train_test_split`.
⚠️ Le ColumnTransformer est `fit` UNIQUEMENT sur X_train (constitution Principe II).

---

### Pipeline scikit-learn

```
Pipeline(
  steps=[
    ('preprocessor', ColumnTransformer([
        ('scaler', StandardScaler(), ['age', 'imc', 'enfants']),
        ('passthrough', 'passthrough', ['sexe', 'fumeur',
                                        'region_northwest',
                                        'region_southeast',
                                        'region_southwest']),
    ])),
    ('model', GradientBoostingRegressor(**best_params, random_state=42)),
  ]
)
```

**Entrée du pipeline** : DataFrame 8 colonnes (format features.csv, sans charges et categorie_risque).
**Sortie du pipeline** : array numpy de prédictions de coûts en USD (float).

---

### Sortie — Fichiers produits

| Fichier | Format | Contenu | Commité |
|---------|--------|---------|---------|
| `ml_models/saved_models/regression.pkl` | Joblib | Pipeline complet (preprocessor + modèle) | ❌ Non (gitignore) |
| `ml_models/saved_models/metadata.json` | JSON | Version, date, algorithme, hyperparamètres, métriques | ✅ Oui |

---

### Interface predict_cost()

**Signature** : `predict_cost(age: int, sexe: int, imc: float, enfants: int, fumeur: int, region: str) -> float`

**Paramètres d'entrée** :

| Paramètre | Type | Valeurs attendues |
|-----------|------|-------------------|
| `age` | int | 18–64 |
| `sexe` | int | 0 (homme) ou 1 (femme) |
| `imc` | float | positif, typiquement 15–55 |
| `enfants` | int | 0–5 |
| `fumeur` | int | 0 (non-fumeur) ou 1 (fumeur) |
| `region` | str | `"northeast"`, `"northwest"`, `"southeast"`, `"southwest"` |

**Flux interne** :
1. Convertir `region` string → 3 colonnes one-hot (via `REGION_MAPPING`)
2. Construire un DataFrame 1-ligne avec les 8 features dans l'ordre attendu par le pipeline
3. Appeler `_pipeline.predict(df)` → retourner `float(prediction[0])`

**Sortie** : `float` — coût médical prédit en USD.

---

### Métriques de performance

| Métrique | Formule | Interprétation |
|----------|---------|----------------|
| R² | 1 - SS_res/SS_tot | Part de variance expliquée. Objectif > 0.80. |
| MAE | mean(\|y_pred - y_true\|) | Erreur absolue moyenne en USD. |
| RMSE | sqrt(mean((y_pred - y_true)²)) | Pénalise les grandes erreurs. En USD. |

---

### Transitions d'état du pipeline (cycle de vie)

```
[Absent] → train_regression.py → [regression.pkl] → predict_cost() → [prédiction float]
                                       ↓
                                 metadata.json
```
