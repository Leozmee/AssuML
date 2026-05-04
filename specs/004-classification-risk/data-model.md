# Data Model: Modèle de Classification — Niveau de Risque

**Feature**: `004-classification-risk` | **Date**: 2026-05-04

---

## Entrée — Dataset d'entraînement

**Source** : `data/processed/features.csv` (identique à la feature 003)

| Colonne | Type | Rôle |
|---------|------|------|
| `age`, `imc`, `enfants` | float/int | Features numériques → StandardScaler |
| `sexe`, `fumeur`, `region_*` (×3) | int | Features binaires/one-hot → passthrough |
| `charges` | float | Ignorée dans cette feature |
| `categorie_risque` | str | **Target classification** — 4 classes |

**Classes cibles** (ordre de sévérité croissante) :

| Classe | Seuil charges | Proportion attendue |
|--------|--------------|---------------------|
| `faible` | < 5 000 USD | ~25% |
| `moyen` | 5 000–15 000 USD | ~50% |
| `eleve` | 15 000–30 000 USD | ~18% |
| `critique` | ≥ 30 000 USD | ~7% |

---

## Pipeline de classification

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
    ('model', GradientBoostingClassifier(**best_params, random_state=42)),
  ]
)
```

**Identique au pipeline de régression** sauf le modèle final. Garantit la cohérence preprocessing entre les deux modèles.

---

## Sorties — Fichiers produits

| Fichier | Format | Contenu | Commité |
|---------|--------|---------|---------|
| `ml_models/saved_models/classification.pkl` | Joblib | Pipeline complet | ❌ Non |
| `ml_models/saved_models/metadata.json` | JSON | Métriques des deux modèles, v1.1.0 | ✅ Oui |

---

## Interface predict_risk()

**Signature** : `predict_risk(age, sexe, imc, enfants, fumeur, region) -> tuple[str, float]`

**Flux interne** (identique à predict_cost() pour la conversion) :
1. Convertir `region` string → 3 colonnes one-hot via `REGION_MAPPING`
2. Construire DataFrame 1-ligne avec les 8 features
3. `categorie = _clf_pipeline.predict(df)[0]` → str
4. `score = max(_clf_pipeline.predict_proba(df)[0])` → float

---

## Modules métier

### business/scoring.py

| Fonction | Signature | Retour |
|----------|-----------|--------|
| `calculer_prime` | `(cout_predit: float, categorie_risque: str) -> float` | `cout_predit × coefficient` |

Coefficients : `faible=1.0`, `moyen=1.15`, `eleve=1.35`, `critique=1.60`

### business/risk_engine.py

| Fonction | Signature | Mapping |
|----------|-----------|---------|
| `get_categorie_risque` | `(cout_predit: float) -> str` | <5000→faible, 5k–15k→moyen, 15k–30k→eleve, ≥30k→critique |
| `get_decision` | `(categorie_risque: str) -> str` | faible/moyen→accepter, eleve→examiner, critique→refuser |

---

## Flux global de décision (feature 001 consommera ces fonctions)

```
Client brut → predict_cost() → cout_predit (float)
           → predict_risk()  → (categorie_risque, score_risque)
                              → calculer_prime(cout_predit, categorie_risque) → prime
                              → get_decision(categorie_risque) → décision
```
