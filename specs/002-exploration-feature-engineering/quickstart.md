# Quickstart : Exploration et Feature Engineering

**Feature**: 002-exploration-feature-engineering
**Date**: 2026-04-07

---

## Prérequis

```bash
# Vérifier la présence du dataset source
ls data/small_data/insurance.csv
# → doit afficher : data/small_data/insurance.csv

# Installer les dépendances si nécessaire
pip install pandas numpy matplotlib seaborn plotly scikit-learn jupyter

# Se placer à la racine du projet
cd /Users/leogallus/Projets/AssuML
```

---

## 1. Exécuter le notebook d'exploration (01)

```bash
# Lancer JupyterLab ou Jupyter Notebook
jupyter lab
# ou
jupyter notebook

# Ouvrir notebooks/01_data_exploration.ipynb
# Kernel → Restart & Run All

# Vérifier la sortie attendue :
# - df.shape → (1338, 7)
# - df.isnull().sum() → 0 sur toutes les colonnes
# - 8+ graphiques avec titres et axes
# - Cellules markdown avec insights entre chaque section
```

**Validation rapide** :
```python
import pandas as pd
df = pd.read_csv('data/small_data/insurance.csv')
assert df.shape == (1338, 7), f"Shape inattendu : {df.shape}"
assert df.isnull().sum().sum() == 0, "Valeurs nulles détectées"
print("✅ Dataset OK")
```

---

## 2. Exécuter le notebook de feature engineering (02)

```bash
# Ouvrir notebooks/02_feature_engineering.ipynb
# Kernel → Restart & Run All

# Vérifier la sortie attendue :
# - Colonnes encodées : sexe (0/1), fumeur (0/1), region_northwest/southeast/southwest
# - Colonne categorie_risque avec 4 valeurs distinctes
# - X_train.shape[0] ≈ 1070, X_test.shape[0] ≈ 268
# - Fichier data/processed/features.csv créé
```

**Validation rapide** :
```python
import pandas as pd
features = pd.read_csv('data/processed/features.csv')
assert 'categorie_risque' in features.columns, "categorie_risque manquante"
assert features['categorie_risque'].nunique() == 4, "Pas 4 catégories"
assert features.shape[0] == 1338, f"Lignes inattendues : {features.shape[0]}"
assert set(features['categorie_risque'].unique()) == {'faible', 'moyen', 'eleve', 'critique'}
print(f"✅ features.csv OK : {features.shape[1]} colonnes, {features.shape[0]} lignes")
print(features['categorie_risque'].value_counts())
```

---

## 3. Tester les scripts de transformation

```bash
# Tests unitaires
pytest tests/unit/test_cleaning.py -v
pytest tests/unit/test_normalization.py -v
```

**Test manuel rapide** :
```python
import pandas as pd
from data_pipeline.transform.cleaning import rename_columns
from data_pipeline.transform.normalization import encode_categoricals

# Charger le dataset brut
df = pd.read_csv('data/small_data/insurance.csv')

# Étape 1 : renommage
df_fr = rename_columns(df)
assert 'sexe' in df_fr.columns and 'sex' not in df_fr.columns
assert 'imc' in df_fr.columns and 'bmi' not in df_fr.columns
print("✅ rename_columns OK")

# Étape 2 : encodage
df_enc = encode_categoricals(df_fr)
assert df_enc['sexe'].isin([0, 1]).all()
assert df_enc['fumeur'].isin([0, 1]).all()
assert 'region_northwest' in df_enc.columns
assert 'region_northeast' not in df_enc.columns  # drop_first
print("✅ encode_categoricals OK")
print(df_enc.dtypes)
```

---

## Vérification complète (smoke test)

```bash
# Tout enchaîner en une commande
python -c "
import pandas as pd
from data_pipeline.transform.cleaning import rename_columns
from data_pipeline.transform.normalization import encode_categoricals

df = pd.read_csv('data/small_data/insurance.csv')
df = rename_columns(df)
df = encode_categoricals(df)
print('Colonnes après encodage:', list(df.columns))
print('Types:', df.dtypes.to_dict())
print('Shape:', df.shape)
"
```

**Sortie attendue** :
```
Colonnes après encodage: ['age', 'sexe', 'imc', 'enfants', 'fumeur', 'charges',
                          'region_northwest', 'region_southeast', 'region_southwest']
Shape: (1338, 9)
```
