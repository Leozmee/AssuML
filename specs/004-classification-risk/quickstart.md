# Quickstart: Modèle de Classification

**Feature**: `004-classification-risk` | **Date**: 2026-05-04

---

## Prérequis

```bash
# Vérifier les fichiers de la feature 003
ls ml_models/saved_models/metadata.json   # doit exister (v1.0.0)
ls data/processed/features.csv            # doit exister (1338 lignes)
python -c "import sklearn, pandas, numpy, joblib; print('OK')"
```

---

## Entraînement classification standalone

```bash
python -m ml_models.training.train_classification

# Sortie attendue :
# ✅ Dataset chargé : 1338 lignes
# --- Métriques finales (GradientBoostingClassifier) ---
# Accuracy : 0.9XXX
# F1-macro  : 0.XXXX
# ✅ classification.pkl sauvegardé
# ✅ metadata.json mis à jour → v1.1.0
```

---

## Utilisation de predict_risk()

```python
from ml_models.prediction.predict import predict_risk

# Profil fumeur à risque élevé
categorie, score = predict_risk(
    age=45, sexe=1, imc=32.0, enfants=2, fumeur=1, region='southeast'
)
print(f"Catégorie : {categorie}")   # 'eleve' ou 'critique'
print(f"Confiance : {score:.2%}")  # ex. 87.3%
```

---

## Utilisation des modules métier

```python
from business.scoring import calculer_prime
from business.risk_engine import get_decision, get_categorie_risque

# Flux complet de souscription
cout_predit = 22000.0          # issu de predict_cost()
categorie = 'eleve'            # issu de predict_risk()

prime = calculer_prime(cout_predit, categorie)
print(f"Prime : {prime:.2f} USD")   # 22000 × 1.35 = 29700

decision = get_decision(categorie)
print(f"Décision : {decision}")      # 'examiner'

# Depuis le coût prédit (sans predict_risk)
cat_engine = get_categorie_risque(cout_predit)
print(f"Catégorie (engine) : {cat_engine}")  # 'eleve'
```

---

## Tests unitaires

```bash
pytest tests/unit/test_classification.py tests/unit/test_business.py -v
# Résultat attendu : tous PASSED
```

---

## Vérification metadata.json

```bash
python -c "
import json
with open('ml_models/saved_models/metadata.json') as f:
    m = json.load(f)
print('Version :', m['version'])          # 1.1.0
print('Régression R² :', m['regression']['metriques_test']['r2'])
print('Classification accuracy :', m['classification']['metriques_test']['accuracy'])
"
```

---

## Fichiers produits

| Fichier | Commité | Description |
|---------|---------|-------------|
| `notebooks/03_model_training.ipynb` | ✅ | Section classification ajoutée |
| `notebooks/04_model_evaluation.ipynb` | ✅ | Évaluation comparative |
| `ml_models/training/train_classification.py` | ✅ | Script standalone |
| `ml_models/prediction/predict.py` | ✅ | predict_risk() ajoutée |
| `business/scoring.py` | ✅ | calculer_prime() |
| `business/risk_engine.py` | ✅ | get_decision(), get_categorie_risque() |
| `tests/unit/test_classification.py` | ✅ | Tests predict_risk() |
| `tests/unit/test_business.py` | ✅ | Tests scoring + risk_engine |
| `ml_models/saved_models/metadata.json` | ✅ | v1.1.0 — deux modèles |
| `ml_models/saved_models/classification.pkl` | ❌ | Gitignored |
