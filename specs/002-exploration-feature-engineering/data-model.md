# Data Model: Exploration et Feature Engineering

**Feature**: 002-exploration-feature-engineering
**Date**: 2026-04-07

---

## Flux de données

```
data/small_data/insurance.csv
          │
          ▼
  [cleaning.py]  rename_columns()
          │
          ▼
  DataFrame nommage français
          │
          ▼
  [normalization.py]  encode_categoricals()
  +  pd.cut() → categorie_risque
  +  train_test_split()
          │
          ▼
  data/processed/features.csv
```

---

## Dataset source : `insurance.csv`

| Colonne | Type brut | Description | Valeurs |
|---------|-----------|-------------|---------|
| `age` | int64 | Âge du bénéficiaire | 18–64 |
| `sex` | object | Sexe | "male", "female" |
| `bmi` | float64 | Indice de masse corporelle | 15.96–53.13 |
| `children` | int64 | Nombre d'enfants couverts | 0–5 |
| `smoker` | object | Statut fumeur | "yes", "no" |
| `region` | object | Région US | "southwest", "southeast", "northwest", "northeast" |
| `charges` | float64 | Coût médical annuel (USD) | 1 121.87–63 770.43 |

**Statistiques clés** :
- 1 338 lignes, 0 valeur nulle
- `charges` : mean=13 270, median=9 382, std=12 110 — distribution très asymétrique
- `smoker` : 20.5% de fumeurs (274/1 338) — déséquilibre à noter

---

## Dataset intermédiaire : nommage français

Après `rename_columns()` :

| Colonne originale | Colonne française | Type |
|-------------------|-------------------|------|
| `age` | `age` | int64 (inchangé) |
| `sex` | `sexe` | object |
| `bmi` | `imc` | float64 |
| `children` | `enfants` | int64 |
| `smoker` | `fumeur` | object |
| `region` | `region` | object (inchangé) |
| `charges` | `charges` | float64 (inchangé) |

---

## Dataset préparé : `features.csv`

Après `encode_categoricals()` + création target + (optionnel) suppression colonnes brutes :

| Colonne | Type | Description | Valeurs possibles |
|---------|------|-------------|-------------------|
| `age` | int64 | Âge | 18–64 |
| `sexe` | int64 | Sexe encodé | 0=homme, 1=femme |
| `imc` | float64 | IMC | 15.96–53.13 |
| `enfants` | int64 | Enfants | 0–5 |
| `fumeur` | int64 | Fumeur encodé | 0=non, 1=oui |
| `charges` | float64 | Coût médical (target régression) | 1 121–63 770 |
| `region_northwest` | int64 | One-hot région | 0 ou 1 |
| `region_southeast` | int64 | One-hot région | 0 ou 1 |
| `region_southwest` | int64 | One-hot région | 0 ou 1 |
| `categorie_risque` | object | Target classification | "faible", "moyen", "eleve", "critique" |

**Référence one-hot** : `region_northeast` supprimé (baseline).
Quand les 3 colonnes region = 0 → le client est dans `northeast`.

---

## Splits train/test

| Split | Lignes | Pourcentage | Usage |
|-------|--------|-------------|-------|
| X_train | ≈ 1 070 | 80% | Entraînement des modèles |
| X_test | ≈ 268 | 20% | Évaluation des modèles |
| y_train_reg | ≈ 1 070 | 80% | Target régression (charges) |
| y_test_reg | ≈ 268 | 20% | Évaluation régression |
| y_train_clf | ≈ 1 070 | 80% | Target classification (categorie_risque) |
| y_test_clf | ≈ 268 | 20% | Évaluation classification |

**Paramètres** : `random_state=42`, `stratify=y_classification`.

---

## Distribution attendue de `categorie_risque`

| Catégorie | Seuil charges | Estimation lignes | % |
|-----------|--------------|-------------------|---|
| faible | < 5 000 | ~335 | ~25% |
| moyen | 5 000–14 999 | ~669 | ~50% |
| eleve | 15 000–29 999 | ~240 | ~18% |
| critique | ≥ 30 000 | ~94 | ~7% |

**Avertissement** : déséquilibre des classes (critique = 7%). À documenter dans
le notebook et à prendre en compte lors de l'entraînement (stratify requis,
métriques par classe obligatoires — constitution Principe II).

---

## Interfaces des fonctions Python

### `cleaning.py`

```python
def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renomme les colonnes du dataset Kaggle vers le nommage métier français.
    
    Paramètres :
        df : DataFrame avec colonnes Kaggle (sex, bmi, children, smoker)
    Retour :
        DataFrame avec colonnes renommées (sexe, imc, enfants, fumeur)
    Note :
        Les colonnes non listées dans le mapping sont conservées telles quelles.
    """
    MAPPING = {
        'sex': 'sexe',
        'bmi': 'imc',
        'children': 'enfants',
        'smoker': 'fumeur'
    }
    return df.rename(columns=MAPPING)
```

### `normalization.py`

```python
def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encode les variables catégorielles pour le machine learning.
    
    Paramètres :
        df : DataFrame avec nommage français (sexe, fumeur, region)
    Retour :
        DataFrame avec encodages binaires et one-hot pour region
    Encodages :
        - sexe : 'femme'→1, 'homme'→0
        - fumeur : 'oui'→1 / 'yes'→1, 'non'→0 / 'no'→0
        - region : one-hot avec drop_first=True (northeast supprimé)
    """
```
