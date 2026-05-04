---

description: "Liste de tâches — Modèle de Régression — Prédiction du Coût Médical"
---

# Tasks: Modèle de Régression — Prédiction du Coût Médical

**Input**: Documents de conception dans `specs/003-regression-model/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Inclus — requis par la constitution (Principe V). Tests unitaires dans `tests/unit/test_regression.py`.

**Organisation**: 4 User Stories — comparaison algos (US1), optimisation/validation (US2),
script standalone + pipeline (US3), fonction predict_cost() production (US4).

## Format: `[ID] [P?] [Story?] Description — fichier cible`

---

## Phase 1 : Setup

**But**: Vérifier les prérequis et initialiser la structure nécessaire.

- [x] T001 Vérifier et créer les `__init__.py` manquants : `ml_models/__init__.py`, `ml_models/training/__init__.py`, `ml_models/prediction/__init__.py` (créer si absent, ne pas écraser si existant)
- [x] T002 [P] Vérifier `data/processed/features.csv` : assert shape == (1338, 10), 0 valeurs nulles, colonnes attendues présentes (`age`, `sexe`, `imc`, `enfants`, `fumeur`, `region_northwest`, `region_southeast`, `region_southwest`, `charges`, `categorie_risque`)
- [x] T003 [P] Vérifier que `ml_models/saved_models/` est dans `.gitignore` (ajouter `ml_models/saved_models/*.pkl` si absent)

**Checkpoint** : Imports Python fonctionnels (`from ml_models.training import train_regression` sans erreur), features.csv valide.

---

## Phase 2 : Fondation (Prérequis bloquants)

**But**: Aucun prérequis bloquant spécifique à cette feature au-delà du Setup.
Le notebook (US1/US2) et le script standalone (US3) peuvent démarrer directement après la Phase 1.

**⚠️ ORDRE STRICT intra-feature** :
- US1 → US2 (l'optimisation porte sur le meilleur algo identifié en US1)
- US2 → US3 (le script encode les hyperparamètres optimaux trouvés en US2)
- US3 → US4 (predict_cost() charge regression.pkl produit par US3)

---

## Phase 3 : User Story 1 — Comparaison des algorithmes de régression (Priority: P1) 🎯 MVP

**But**: Entraîner et comparer LinearRegression, RandomForestRegressor, GradientBoostingRegressor.
Produire un tableau de métriques (R², MAE, RMSE) et identifier le meilleur modèle.

**Test indépendant** : `Kernel → Restart & Run All` sur `notebooks/03_model_training.ipynb`.
Vérifier : tableau comparatif 3 lignes × 3 métriques, cellule markdown du choix justifié, scatter plot + résidus présents.

### Implémentation US1

- [x] T004 [US1] Créer `notebooks/03_model_training.ipynb` — Section 1 : imports (pandas, numpy, matplotlib, seaborn, sklearn), chargement `data/processed/features.csv`, définition `feature_cols = ['age','sexe','imc','enfants','fumeur','region_northwest','region_southeast','region_southwest']`, `X = df[feature_cols]`, `y = df['charges']`, `train_test_split(X, y, test_size=0.2, random_state=42)`, affichage shapes avec assert `X_train.shape[0] + X_test.shape[0] == 1338`
- [x] T005 [US1] Ajouter Section 2 dans le notebook — Entraînement des 3 modèles avec ColumnTransformer (StandardScaler sur `['age','imc','enfants']`, passthrough sur les 5 autres colonnes) : `LinearRegression`, `RandomForestRegressor(random_state=42)`, `GradientBoostingRegressor(random_state=42)` — pour chacun calculer R², MAE, RMSE sur le test set et stocker dans un dict `results`
- [x] T006 [US1] Ajouter Section 3 dans le notebook — Tableau comparatif `pd.DataFrame(results).T.sort_values('R²', ascending=False)` affiché + cellule markdown identifiant le meilleur algorithme avec justification chiffrée (ex. "GradientBoostingRegressor retenu : R²=X.XX, MAE=X XXX USD")
- [x] T007 [US1] Ajouter Section 4 dans le notebook — Graphique 1 : scatter "Valeurs réelles vs Prédictions" (`plt.scatter(y_test, y_pred)` + droite identité en rouge, titre "Prédictions vs Valeurs Réelles", axes labellisés) ; Graphique 2 : distribution des résidus (`residuals = y_test - y_pred`, `sns.histplot(residuals, kde=True)`, titre "Distribution des Résidus", ligne verticale à 0) — les deux avec `plt.tight_layout()`

**Checkpoint** : US1 complète — notebook exécutable, 3 modèles comparés, meilleur identifié, 2 graphiques produits.

---

## Phase 4 : User Story 2 — Optimisation et validation approfondie (Priority: P1)

**But**: Optimiser le meilleur modèle via GridSearchCV (4 hyperparamètres), valider par
cross-validation 5 plis (R² moyen > 0.80), et calculer la feature importance.

**Test indépendant** : Dans le notebook, vérifier : `best_params_` affiché, 5 scores CV individuels + moyenne ± écart-type affichés, `cv_mean > 0.80`, graphique feature importance horizontal présent.

### Implémentation US2

- [x] T008 [US2] Ajouter Section 5 dans le notebook — GridSearchCV sur le meilleur modèle avec grille : `param_grid = {'model__n_estimators': [100, 200], 'model__max_depth': [3, 4, 5], 'model__min_samples_split': [2, 5], 'model__min_samples_leaf': [1, 2]}`, `GridSearchCV(pipeline, param_grid, cv=5, scoring='r2', n_jobs=-1)`, afficher `grid_search.best_params_` et `grid_search.best_score_` + cellule markdown avec les hyperparamètres retenus
- [x] T009 [US2] Ajouter Section 6 dans le notebook — Cross-validation 5 plis sur le modèle optimisé complet (X entier, y entier) : `cv_scores = cross_val_score(best_pipeline, X, y, cv=5, scoring='r2')`, afficher les 5 scores individuels + `f"R² moyen : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}"` + `assert cv_scores.mean() > 0.80, f"Objectif R²>0.80 non atteint : {cv_scores.mean():.4f}"`
- [x] T010 [US2] Ajouter Section 7 dans le notebook — Feature importance : extraire `best_pipeline.named_steps['model'].feature_importances_`, créer DataFrame `pd.DataFrame({'feature': feature_cols, 'importance': importances}).sort_values('importance')`, graphique `plt.barh()` horizontal avec titre "Importance des Variables", axes labellisés, + cellule markdown nommant les 3 variables les plus importantes
- [x] T011 [US2] Vérifier `Kernel → Restart & Run All` sur le notebook complet — corriger toute erreur résiduelle, vérifier que les 4+ graphiques ont tous des titres et axes labellisés

**Checkpoint** : US2 complète — notebook entièrement validé, R² moyen CV > 0.80, feature importance calculée.

---

## Phase 5 : User Story 3 — Script standalone et sauvegarde du pipeline (Priority: P1)

**But**: Créer `train_regression.py` exécutable en standalone avec `python -m ml_models.training.train_regression`.
Produit `regression.pkl` (Pipeline complet) et `metadata.json` (métriques + hyperparamètres).

**Test indépendant** : `python -m ml_models.training.train_regression` s'exécute sans erreur, affiche R²/MAE/RMSE, crée `ml_models/saved_models/regression.pkl` et `metadata.json`. Vérifier : `joblib.load('ml_models/saved_models/regression.pkl')` retourne un Pipeline sklearn.

### Implémentation US3

- [x] T012 [US3] Créer `ml_models/training/train_regression.py` — docstring en français, imports, chargement `data/processed/features.csv` avec `FileNotFoundError` explicite si absent, définition `feature_cols` et `target_col = 'charges'`, `train_test_split(X, y, test_size=0.2, random_state=42)`, affichage `f"✅ Dataset chargé : {len(df)} lignes, X_train={X_train.shape[0]}, X_test={X_test.shape[0]}"`
- [x] T013 [US3] Ajouter dans `train_regression.py` — ColumnTransformer (StandardScaler sur `['age','imc','enfants']`, passthrough sur `['sexe','fumeur','region_northwest','region_southeast','region_southwest']`), Pipeline avec GradientBoostingRegressor et les hyperparamètres optimaux trouvés en US2, entraînement `pipeline.fit(X_train, y_train)`, calcul R²/MAE/RMSE sur X_test, affichage formaté
- [x] T014 [US3] Ajouter dans `train_regression.py` — `os.makedirs('ml_models/saved_models', exist_ok=True)`, `joblib.dump(pipeline, 'ml_models/saved_models/regression.pkl')`, création et sauvegarde `metadata.json` avec champs : `version`, `date_entrainement`, `algorithme`, `hyperparametres`, `metriques_test` (r2/mae/rmse), `metriques_cv` (r2_mean/r2_std depuis cross_val_score 5 plis), `features`, `target`, `split`, `random_state` — afficher `"✅ Pipeline et metadata sauvegardés"`
- [x] T015 [US3] Ajouter bloc `if __name__ == '__main__': main()` dans `train_regression.py` et vérifier l'exécution complète : `python -m ml_models.training.train_regression` — corriger toute erreur

**Checkpoint** : US3 complète — `regression.pkl` et `metadata.json` créés, script autonome fonctionnel.

---

## Phase 6 : User Story 4 — Fonction predict_cost() production (Priority: P2)

**But**: Exposer `predict_cost(age, sexe, imc, enfants, fumeur, region)` dans
`ml_models/prediction/predict.py`, avec chargement singleton du pipeline et conversion
region string → one-hot interne.

**Test indépendant** : `pytest tests/unit/test_regression.py -v` → 4 tests PASSED.
`from ml_models.prediction.predict import predict_cost; print(predict_cost(45, 1, 32.0, 2, 1, 'southeast'))` → float > 20 000.

### Tests US4

- [x] T016 [P] [US4] Créer `tests/unit/test_regression.py` — 4 tests : (1) `test_predict_cost_returns_float` : appel avec profil valide → retourne float positif ; (2) `test_predict_cost_smoker_higher` : `predict_cost(..., fumeur=1, ...)` > `predict_cost(..., fumeur=0, ...)` à profil identique ; (3) `test_predict_cost_all_regions` : appel avec chacune des 4 régions sans erreur ; (4) `test_predict_cost_missing_pkl` : renommer temporairement le pkl, vérifier `FileNotFoundError` ou `OSError` explicite

### Implémentation US4

- [x] T017 [US4] Créer `ml_models/prediction/predict.py` — docstring en français, imports (`joblib`, `pandas`, `os`), constante `MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'saved_models', 'regression.pkl')`, `REGION_MAPPING` dict (4 régions → dict 3 colonnes one-hot), chargement singleton `_pipeline = None` avec fonction `_load_pipeline()` qui lève `FileNotFoundError(f"Modèle introuvable : {MODEL_PATH}")` si absent
- [x] T018 [US4] Ajouter dans `predict.py` — fonction `predict_cost(age: int, sexe: int, imc: float, enfants: int, fumeur: int, region: str) -> float` avec docstring en français documentant chaque paramètre et les valeurs attendues, conversion `region` via `REGION_MAPPING`, construction DataFrame 1-ligne avec les 8 colonnes dans l'ordre `feature_cols`, appel `_load_pipeline().predict(df)`, retour `float(pred[0])`
- [x] T019 [US4] Exécuter `pytest tests/unit/test_regression.py -v` et corriger jusqu'à 4/4 PASSED

**Checkpoint** : US4 complète — `predict_cost()` importable, testée, fonctionnelle.

---

## Phase finale : Polish & conformité

**But**: Validation PEP8, vérification metadata.json, conformité constitution.

- [x] T020 [P] Vérifier PEP8 et formatter : `flake8 ml_models/ --max-line-length=88` puis `black ml_models/` — corriger les erreurs residuelles
- [x] T021 [P] Vérifier `ml_models/saved_models/metadata.json` : tous les champs requis présents (`version`, `date_entrainement`, `algorithme`, `hyperparametres`, `metriques_test`, `metriques_cv`, `features`, `target`, `split`, `random_state`) — le fichier DOIT être commité
- [x] T022 [P] Vérifier que `ml_models/saved_models/regression.pkl` est bien dans `.gitignore` (pas de `.pkl` dans `git status` / `git diff --cached`)
- [x] T023 Vérifier `Kernel → Restart & Run All` final sur `notebooks/03_model_training.ipynb` — notebook complet < 5 minutes, R² affiché > 0.80, aucune erreur
- [x] T024 [P] Vérifier la cohérence entre les hyperparamètres dans `metadata.json` et ceux du Pipeline dans `train_regression.py` (même valeurs)

---

## Dépendances et ordre d'exécution

### Dépendances entre phases

- **Phase 1 (Setup)** : Aucune dépendance — démarre immédiatement.
- **US1 (Phase 3)** : Dépend de Phase 1. Peut démarrer dès T001–T003 terminés.
- **US2 (Phase 4)** : Dépend de US1 — l'optimisation porte sur le meilleur algo identifié.
- **US3 (Phase 5)** : Dépend de US2 — le script encode les hyperparamètres optimaux.
- **US4 (Phase 6)** : Dépend de US3 — `predict_cost()` charge `regression.pkl`.
- **Polish** : Dépend de US1 + US2 + US3 + US4.

### Dépendances intra-US (ordre strict)

- **US1** : T004 → T005 → T006 → T007 (sections notebook séquentielles)
- **US2** : T008 → T009 → T010 → T011 (dépend de US1 terminée)
- **US3** : T012 → T013 → T014 → T015 (même fichier, ajouts successifs)
- **US4** : T016 (tests) en parallèle avec T017 → T018 → T019

### Opportunités de parallélisme

- **Phase 1** : T001, T002, T003 en parallèle (fichiers distincts).
- **US4** : T016 (test file) peut être écrit en parallèle avec T017 (predict.py).
- **Polish** : T020, T021, T022, T024 en parallèle.
- **Notebooks vs Script** : Une fois US2 terminée, US3 (script) peut démarrer pendant que le notebook est finalisé.

---

## Exemple de parallélisme

### Phase 1 — Setup

```bash
# Simultanément :
Task: "Vérifier/créer __init__.py"          # T001
Task: "Vérifier features.csv"               # T002
Task: "Vérifier .gitignore"                 # T003
```

### US4 — predict_cost()

```bash
# Simultanément :
Task: "Créer tests/unit/test_regression.py" # T016
Task: "Créer ml_models/prediction/predict.py (skeleton)"  # T017
# Puis séquentiellement :
Task: "Implémenter predict_cost()"          # T018
Task: "pytest -v"                           # T019
```

---

## Stratégie d'implémentation

### MVP First (US1 uniquement)

1. Phase 1 (Setup) — vérification rapide
2. US1 — notebook sections 1–4 (chargement + comparaison + graphiques)
3. **STOP et VALIDATION** : Restart & Run All, tableau comparatif présent, meilleur algo identifié
4. Démo MVP : notebook EDA + comparaison d'algorithmes prêt

### Livraison complète

1. Phase 1 → Setup OK
2. US1 → Comparaison 3 algos → notebook section 1–4
3. US2 → GridSearchCV + CV 5-fold + feature importance → notebook complet validé
4. US3 → Script standalone → regression.pkl + metadata.json
5. US4 → predict_cost() → tests pytest 4/4 PASSED
6. Polish → PEP8 + metadata check + gitignore

---

## Notes

- `[P]` = peut s'exécuter en parallèle (fichiers distincts, pas de dépendances)
- `[USn]` = traçabilité vers la User Story dans spec.md
- `random_state=42` OBLIGATOIRE sur tous les appels stochastiques
- `regression.pkl` JAMAIS commité (constitution Principe IV)
- `metadata.json` TOUJOURS commité (pas de données sensibles)
- Le ColumnTransformer est `fit` UNIQUEMENT sur X_train (constitution Principe II)
- La constitution exige au moins 1 test pytest par fonctionnalité livrée (Principe V)
