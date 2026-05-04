# Research: Modèle de Classification — Niveau de Risque

**Feature**: `004-classification-risk` | **Date**: 2026-05-04

---

## Décision 1 — Algorithme vainqueur attendu

**Décision** : GradientBoostingClassifier sera très probablement le meilleur des deux.

**Rationale** : La variable cible `categorie_risque` est directement dérivée de `charges` par tranches. Le GBR de régression atteignait R²=0.85 sur `charges`, ce qui signifie que les mêmes non-linéarités (fumeur×IMC) sont aussi présentes pour la classification. GradientBoosting excelle sur les frontières de décision complexes avec des classes déséquilibrées. Sur ce dataset, accuracy attendue : RF ~0.87, GBC ~0.90.

**Alternatives considérées** :
- RandomForestClassifier : bon mais légèrement moins précis sur les classes rares (critique ~7%)
- LogisticRegression : trop linéaire — rejeté (non demandé dans la spec)

---

## Décision 2 — Gestion de la target categorie_risque

**Décision** : Laisser `categorie_risque` comme string dans le Pipeline sklearn. Les classificateurs d'ensemble (RF, GBC) acceptent les labels string nativement. Pas de LabelEncoder dans le pipeline.

**Rationale** : LabelEncoder dans un Pipeline sklearn présente des risques de fuite de données si mal placé. Les `RandomForestClassifier` et `GradientBoostingClassifier` de sklearn gèrent les labels non numériques depuis la version 1.0+. Le pipeline retournera directement les strings originales.

**Exception** : pour les courbes ROC, `label_binarize` est appliqué **hors pipeline** avec ordre fixe `['faible', 'moyen', 'eleve', 'critique']`. Cet ordre est celui de sévérité croissante — il est documenté et figé.

**Alternatives considérées** :
- LabelEncoder dans le pipeline : complexifie la récupération des noms de classes — rejeté
- OrdinalEncoder : encode en entiers ordonnés, perd les noms — rejeté

---

## Décision 3 — Courbe ROC multiclasse

**Décision** : `OneVsRestClassifier(best_pipeline)` + `label_binarize` + une `roc_curve` par classe.

```python
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import label_binarize

CLASSES_ORDER = ['faible', 'moyen', 'eleve', 'critique']
y_bin = label_binarize(y_test, classes=CLASSES_ORDER)

ovr = OneVsRestClassifier(best_pipeline)
ovr.fit(X_train, y_train)
y_score = ovr.predict_proba(X_test)

# Une courbe par classe + macro-average
for i, classe in enumerate(CLASSES_ORDER):
    fpr, tpr, _ = roc_curve(y_bin[:, i], y_score[:, i])
    auc = roc_auc_score(y_bin[:, i], y_score[:, i])
```

**Rationale** : Approche standard sklearn pour ROC multiclasse. `OneVsRestClassifier` wrapping le pipeline complet garantit que le preprocessing est appliqué dans chaque fold OvR. Alternative directe avec `predict_proba` du pipeline existant est aussi valide mais moins explicite pédagogiquement.

---

## Décision 4 — Grille GridSearchCV classification

**Décision** :

```python
param_grid = {
    'model__n_estimators': [100, 200],
    'model__max_depth': [3, 5, None],
    'model__min_samples_split': [2, 5],
}
# cv=5, scoring='accuracy', n_jobs=-1
# 2×3×2 = 12 combinaisons × 5 folds = 60 fits
```

**Rationale** : 60 fits sur 1 338 lignes ≈ 30–45 secondes. Couvre les 3 hyperparamètres minimum requis (FR-005). `max_depth=None` pour tester un arbre non contraint vs profondeurs limitées.

---

## Décision 5 — calculer_prime() : signature et coefficients

**Décision** :

```python
COEFFICIENTS = {'faible': 1.0, 'moyen': 1.15, 'eleve': 1.35, 'critique': 1.60}

def calculer_prime(cout_predit: float, categorie_risque: str) -> float:
    return cout_predit * COEFFICIENTS[categorie_risque]
```

**Rationale** : Signature plus claire que `(cout_predit, score_risque)` mentionnée dans la spec initiale — le coefficient est déterministe par catégorie (pas par score flottant). Cohérent avec la constitution AssuML qui définit les 4 coefficients. `score_risque` (float de confiance) n'est pas utilisé dans le calcul de prime — il est exposé pour l'affichage dans le module Scoring Streamlit.

---

## Décision 6 — metadata.json : structure fusionnée

**Décision** : structure à deux clés de premier niveau `regression` et `classification`, version globale `1.1.0`.

```json
{
  "version": "1.1.0",
  "date_mise_a_jour": "2026-05-04",
  "regression": {
    "version": "1.0.0",
    "date_entrainement": "...",
    "algorithme": "GradientBoostingRegressor",
    "hyperparametres": {...},
    "metriques_test": {"r2": 0.8533, "mae": 2666.63, "rmse": 4771.56},
    "metriques_cv": {"r2_mean": 0.8315, "r2_std": 0.0429}
  },
  "classification": {
    "version": "1.0.0",
    "date_entrainement": "...",
    "algorithme": "GradientBoostingClassifier",
    "hyperparametres": {...},
    "metriques_test": {"accuracy": ..., "f1_macro": ...},
    "metriques_cv": {"accuracy_mean": ..., "accuracy_std": ...}
  },
  "features": [...],
  "target_regression": "charges",
  "target_classification": "categorie_risque",
  "split": "80/20",
  "random_state": 42
}
```

**Rationale** : Séparation claire des deux modèles, préservation des métriques régression existantes, lisibilité pour le module Monitoring Streamlit (US8 feature 001).

---

## Aucun NEEDS CLARIFICATION

Tous les choix techniques ont été résolus par les contraintes explicites de l'utilisateur (`/speckit-plan` args) et la constitution AssuML.
