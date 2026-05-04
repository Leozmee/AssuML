# Quickstart: Modèle de Régression

**Feature**: `003-regression-model` | **Date**: 2026-05-04

---

## Prérequis

```bash
# Vérifier la présence du dataset préparé (produit par feature 002)
ls data/processed/features.csv
# → doit afficher le fichier (1 338 lignes)

# Vérifier les dépendances
python -c "import sklearn, pandas, numpy, joblib, matplotlib, seaborn; print('OK')"
```

---

## Exécution du notebook (exploration + optimisation)

```bash
# Lancer Jupyter
jupyter notebook notebooks/03_model_training.ipynb

# Ou JupyterLab
jupyter lab notebooks/03_model_training.ipynb

# Validation : Kernel → Restart & Run All
# Durée attendue : < 5 minutes
# Vérifier : tableau comparatif 3 algos, R² > 0.80 pour le meilleur, 4+ graphiques
```

---

## Entraînement standalone (production)

```bash
# Depuis la racine du projet
python -m ml_models.training.train_regression

# Sortie attendue :
# ✅ Dataset chargé : 1338 lignes, 8 features
# ✅ Split : X_train=1070, X_test=268
# --- Métriques finales (GradientBoostingRegressor) ---
# R²   : 0.8XXX
# MAE  : XXXX.XX USD
# RMSE : XXXX.XX USD
# ✅ Pipeline sauvegardé : ml_models/saved_models/regression.pkl
# ✅ Metadata sauvegardée : ml_models/saved_models/metadata.json
```

---

## Vérification du modèle sauvegardé

```python
import joblib
import pandas as pd

# Charger le pipeline
pipeline = joblib.load('ml_models/saved_models/regression.pkl')

# Test rapide
X_test = pd.DataFrame([{
    'age': 45, 'sexe': 1, 'imc': 32.0, 'enfants': 2,
    'fumeur': 1, 'region_northwest': 0,
    'region_southeast': 1, 'region_southwest': 0
}])
pred = pipeline.predict(X_test)
print(f"Coût prédit : {pred[0]:.2f} USD")  # Attendu > 20 000 USD (fumeur, imc élevé)
```

---

## Utilisation de predict_cost()

```python
from ml_models.prediction.predict import predict_cost

# Profil fumeur — coût attendu élevé
cout_fumeur = predict_cost(age=45, sexe=1, imc=32.0, enfants=2, fumeur=1, region='southeast')
print(f"Fumeur : {cout_fumeur:.2f} USD")  # > 20 000 USD attendu

# Même profil non-fumeur — coût attendu faible
cout_non_fumeur = predict_cost(age=45, sexe=1, imc=32.0, enfants=2, fumeur=0, region='southeast')
print(f"Non-fumeur : {cout_non_fumeur:.2f} USD")  # < 10 000 USD attendu

# Vérifier : cout_fumeur > cout_non_fumeur
assert cout_fumeur > cout_non_fumeur, "Erreur : le fumeur devrait coûter plus cher"
```

---

## Tests unitaires

```bash
# Exécuter les tests
pytest tests/unit/test_regression.py -v

# Résultat attendu :
# PASSED tests/unit/test_regression.py::test_predict_cost_returns_float
# PASSED tests/unit/test_regression.py::test_predict_cost_smoker_higher
# PASSED tests/unit/test_regression.py::test_predict_cost_all_regions
# PASSED tests/unit/test_regression.py::test_predict_cost_missing_pkl
```

---

## Vérification qualité

```bash
# PEP8
flake8 ml_models/ --max-line-length=88
black --check ml_models/

# Formatter si nécessaire
black ml_models/
```

---

## Fichiers produits

| Fichier | Commité | Description |
|---------|---------|-------------|
| `notebooks/03_model_training.ipynb` | ✅ | Notebook exploration + optimisation |
| `ml_models/training/train_regression.py` | ✅ | Script standalone |
| `ml_models/prediction/predict.py` | ✅ | Fonction predict_cost() |
| `ml_models/saved_models/metadata.json` | ✅ | Métriques + hyperparamètres |
| `ml_models/saved_models/regression.pkl` | ❌ | Pipeline binaire (gitignored) |
| `tests/unit/test_regression.py` | ✅ | Tests unitaires |
