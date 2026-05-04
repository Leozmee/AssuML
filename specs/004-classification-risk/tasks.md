---

description: "Liste de tâches — Modèle de Classification — Niveau de Risque Assuré"
---

# Tasks: Modèle de Classification — Niveau de Risque Assuré

**Input**: Documents de conception dans `specs/004-classification-risk/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Inclus — requis par la constitution (Principe V).
Tests unitaires dans `tests/unit/test_classification.py` et `tests/unit/test_business.py`.

**Organisation**: 4 User Stories — classification notebook (US1), script standalone (US2),
predict_risk() + modules métier (US3), notebook évaluation comparative (US4).

## Format: `[ID] [P?] [Story?] Description — fichier cible`

---

## Phase 1 : Setup

**But**: Vérifier les prérequis et initialiser la structure `business/`.

- [X] T001 Créer `business/__init__.py`, `business/scoring.py` (vide), `business/risk_engine.py` (vide) — répertoire `business/` créé si absent
- [X] T002 [P] Vérifier `data/processed/features.csv` — assert shape==(1338,10), colonne `categorie_risque` présente avec exactement 4 valeurs uniques (faible, moyen, eleve, critique)
- [X] T003 [P] Vérifier `ml_models/saved_models/metadata.json` — assert version == "1.0.0", clé `regression` présente avec `metriques_test.r2` > 0.80

**Checkpoint** : `business/` importable, features.csv et metadata.json v1.0.0 validés.

---

## Phase 2 : Fondation (Prérequis bloquants)

**But**: Aucun prérequis bloquant au-delà du Setup.

**⚠️ ORDRE STRICT intra-feature** :
- US1 → US2 (le script encode les hyperparamètres optimaux trouvés en US1)
- US2 → US3 (predict_risk() charge classification.pkl produit par US2)
- US1 + US2 → US4 (le notebook 04 charge metadata.json v1.1.0 produit par US2)

---

## Phase 3 : User Story 1 — Classification dans le notebook d'entraînement (Priority: P1) 🎯 MVP

**But**: Ajouter la section classification dans `notebooks/03_model_training.ipynb` :
comparer RandomForestClassifier et GradientBoostingClassifier, optimiser le meilleur,
afficher matrice de confusion heatmap, courbes ROC one-vs-rest, feature importance.

**Test indépendant** : `Kernel → Restart & Run All` sur `notebooks/03_model_training.ipynb`.
Vérifier : rapport de classification avec accuracy > 0.85 pour le meilleur modèle, heatmap 4×4 présente, 4 courbes ROC + macro-average, score CV moyen > 0.85.

### Implémentation US1

- [X] T004 [US1] Ajouter Section 8 dans `notebooks/03_model_training.ipynb` — titre "Classification : Prédiction de la Catégorie de Risque", imports additionnels (`RandomForestClassifier`, `GradientBoostingClassifier`, `classification_report`, `confusion_matrix`, `roc_curve`, `roc_auc_score`, `label_binarize`, `OneVsRestClassifier`), chargement `y_clf = df['categorie_risque']`, split identique : `X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(X, y_clf, test_size=0.2, random_state=42)`, affichage `value_counts(normalize=True)` de y_clf
- [X] T005 [US1] Ajouter Section 9 dans `notebooks/03_model_training.ipynb` — entraîner `RandomForestClassifier(random_state=42)` et `GradientBoostingClassifier(random_state=42)` chacun dans un Pipeline identique à la régression (même ColumnTransformer), afficher `classification_report` de chaque modèle avec labels=['faible','moyen','eleve','critique'], identifier le meilleur par accuracy sur le test set, cellule markdown de justification
- [X] T006 [US1] Ajouter Section 10 dans `notebooks/03_model_training.ipynb` — GridSearchCV sur le meilleur classificateur avec grille `{'model__n_estimators': [100, 200], 'model__max_depth': [3, 5, None], 'model__min_samples_split': [2, 5]}`, `cv=5, scoring='accuracy', n_jobs=-1`, afficher `best_params_` + `best_score_` + cellule markdown des hyperparamètres retenus
- [X] T007 [US1] Ajouter Section 11 dans `notebooks/03_model_training.ipynb` — cross-validation 5 plis : `cv_scores_clf = cross_val_score(best_clf_pipeline, X, y_clf, cv=5, scoring='accuracy', n_jobs=-1)`, afficher les 5 scores + moyenne ± écart-type, `assert cv_scores_clf.mean() > 0.85`
- [X] T008 [US1] Ajouter Section 12 dans `notebooks/03_model_training.ipynb` — matrice de confusion heatmap : `cm = confusion_matrix(y_test_c, y_pred_c, labels=['faible','moyen','eleve','critique'])`, `sns.heatmap(cm, annot=True, fmt='d', xticklabels=[...], yticklabels=[...], cmap='Blues')`, titre "Matrice de Confusion — [Meilleur algo]", axes labellisés "Prédit" / "Réel"
- [X] T009 [US1] Ajouter Section 13 dans `notebooks/03_model_training.ipynb` — courbes ROC one-vs-rest : `CLASSES_ORDER = ['faible','moyen','eleve','critique']`, `y_bin = label_binarize(y_test_c, classes=CLASSES_ORDER)`, wrapper `OneVsRestClassifier(best_clf_pipeline).fit(X_train_c, y_train_c)`, `y_score = ovr.predict_proba(X_test_c)`, boucle sur les 4 classes pour tracer `roc_curve` + AUC, + courbe macro-average, titre "Courbes ROC One-vs-Rest"
- [X] T010 [US1] Ajouter Section 14 dans `notebooks/03_model_training.ipynb` — feature importance du meilleur classificateur : graphique horizontal `plt.barh()` trié par importance décroissante, titre "Importance des Variables — Classification", + cellule markdown top 3 variables

**Checkpoint** : US1 complète — notebook avec section classification entièrement validée (Restart & Run All sans erreur, accuracy CV > 0.85).

---

## Phase 4 : User Story 2 — Script standalone et pipeline classification (Priority: P1)

**But**: Créer `train_classification.py` exécutable en standalone. Produit `classification.pkl`
et met à jour `metadata.json` v1.1.0 avec les métriques des deux modèles.

**Test indépendant** : `python -m ml_models.training.train_classification` sans erreur.
Vérifier : `classification.pkl` créé, `metadata.json` version=="1.1.0", clés `regression` et `classification` présentes.

### Implémentation US2

- [X] T011 [US2] Créer `ml_models/training/train_classification.py` — docstring en français, constantes `DATA_PATH`, `MODEL_DIR`, `CLF_PATH`, `METADATA_PATH`, `FEATURE_COLS`, `TARGET_CLF`, `NUMERIC_COLS`, `PASSTHROUGH_COLS`, `BEST_PARAMS` (hyperparamètres optimaux de US1), `RANDOM_STATE=42`, `CLASSES_ORDER=['faible','moyen','eleve','critique']`
- [X] T012 [US2] Ajouter fonctions dans `train_classification.py` : `charger_donnees()` (FileNotFoundError si absent), `construire_pipeline()` (même ColumnTransformer que régression + GradientBoostingClassifier), `calculer_metriques_clf(y_true, y_pred)` → dict avec accuracy/f1_macro/precision_macro/recall_macro
- [X] T013 [US2] Ajouter fonction `mettre_a_jour_metadata(metriques_test, metriques_cv, best_params)` dans `train_classification.py` — lire `metadata.json` existant, ajouter clé `classification` avec version/date/algorithme/hyperparamètres/métriques_test/métriques_cv, mettre version globale à "1.1.0", `date_mise_a_jour` à today(), réécrire le fichier
- [X] T014 [US2] Ajouter fonction `main()` et bloc `if __name__ == '__main__'` dans `train_classification.py` — fit pipeline, calcul métriques test, cross-validation 5 plis accuracy, `joblib.dump`, appel `mettre_a_jour_metadata`, affichage récapitulatif formaté
- [X] T015 [US2] Vérifier l'exécution : `python -m ml_models.training.train_classification` → `classification.pkl` et `metadata.json` v1.1.0 créés, accuracy affichée > 0.85

**Checkpoint** : US2 complète — pipeline de classification opérationnel, metadata.json consolidé.

---

## Phase 5 : User Story 3 — predict_risk() et modules métier (Priority: P1)

**But**: Ajouter `predict_risk()` dans `predict.py` (singleton `classification.pkl`), créer
`business/scoring.py` avec `calculer_prime()`, créer `business/risk_engine.py` avec
`get_categorie_risque()` et `get_decision()`.

**Test indépendant** : `pytest tests/unit/test_classification.py tests/unit/test_business.py -v` → tous PASSED.

### Tests US3

- [X] T016 [P] [US3] Créer `tests/unit/test_classification.py` — 4 tests : (1) `test_predict_risk_returns_tuple` : retourne tuple (str, float) ; (2) `test_predict_risk_smoker_eleve_or_critique` : fumeur, imc=32 → catégorie 'eleve' ou 'critique' ; (3) `test_predict_risk_all_regions` : 4 régions sans erreur ; (4) `test_predict_risk_missing_pkl` : FileNotFoundError si clf absent
- [X] T017 [P] [US3] Créer `tests/unit/test_business.py` — 6 tests : (1–4) `test_calculer_prime_[categorie]` : coefficients 1.0/1.15/1.35/1.60 par catégorie ; (5) `test_get_decision_mapping` : 4 catégories → 3 décisions correctes ; (6) `test_get_decision_invalid` : ValueError pour catégorie inconnue ; + 4 tests `test_get_categorie_risque_[seuil]` : valeurs limites 4999/5000/14999/15000/29999/30000

### Implémentation US3

- [X] T018 [US3] Ajouter dans `ml_models/prediction/predict.py` — constante `CLF_PATH` (chemin vers classification.pkl), singleton `_clf_pipeline = None`, fonction `_load_clf_pipeline()` avec FileNotFoundError explicite
- [X] T019 [US3] Ajouter dans `ml_models/prediction/predict.py` — fonction `predict_risk(age, sexe, imc, enfants, fumeur, region) -> tuple[str, float]` avec docstring français, même conversion REGION_MAPPING que predict_cost(), DataFrame 1-ligne, `categorie = _load_clf_pipeline().predict(df)[0]`, `score = float(max(_load_clf_pipeline().predict_proba(df)[0]))`, retourner `(str(categorie), score)`
- [X] T020 [P] [US3] Créer `business/scoring.py` — docstring module en français, `COEFFICIENTS = {'faible': 1.0, 'moyen': 1.15, 'eleve': 1.35, 'critique': 1.60}`, fonction `calculer_prime(cout_predit: float, categorie_risque: str) -> float` avec docstring français, `return cout_predit * COEFFICIENTS[categorie_risque]`, KeyError si catégorie inconnue
- [X] T021 [P] [US3] Créer `business/risk_engine.py` — docstring module en français, `SEUILS = [(5000, 'faible'), (15000, 'moyen'), (30000, 'eleve')]`, fonction `get_categorie_risque(cout_predit: float) -> str` avec docstring français (seuils : <5000→faible, 5000–15000→moyen, 15000–30000→eleve, ≥30000→critique) ; fonction `get_decision(categorie_risque: str) -> str` avec docstring français (faible/moyen→accepter, eleve→examiner, critique→refuser, ValueError sinon)
- [X] T022 [US3] Exécuter `pytest tests/unit/test_classification.py tests/unit/test_business.py -v` et corriger jusqu'à tous PASSED

**Checkpoint** : US3 complète — predict_risk() testée, modules métier fonctionnels.

---

## Phase 6 : User Story 4 — Notebook d'évaluation comparative (Priority: P2)

**But**: Créer `notebooks/04_model_evaluation.ipynb` avec tableau comparatif régression/classification,
learning curves des deux modèles, analyse overfitting, conclusions.

**Test indépendant** : `Kernel → Restart & Run All` sur `notebooks/04_model_evaluation.ipynb`.
Vérifier : tableau récapitulatif 2 modèles, 2 learning curves, cellule markdown overfitting, notebook exécutable sans erreur.

### Implémentation US4

- [X] T023 [US4] Créer `notebooks/04_model_evaluation.ipynb` — Section 1 : imports, chargement `metadata.json`, affichage tableau récapitulatif `pd.DataFrame` côte-à-côte avec colonnes Régression (R², MAE, RMSE, algo, hyperparamètres) et Classification (accuracy, F1-macro, algo, hyperparamètres), cellule markdown de synthèse
- [X] T024 [US4] Ajouter Section 2 dans `notebooks/04_model_evaluation.ipynb` — learning curve régression : `learning_curve(pipeline_reg, X, y_reg, cv=5, scoring='r2', train_sizes=np.linspace(0.1,1.0,10), n_jobs=-1)`, graphique train vs validation score en fonction de n_samples, titre "Learning Curve — Régression", axes labellisés
- [X] T025 [US4] Ajouter Section 3 dans `notebooks/04_model_evaluation.ipynb` — learning curve classification : `learning_curve(pipeline_clf, X, y_clf, cv=5, scoring='accuracy', train_sizes=np.linspace(0.1,1.0,10), n_jobs=-1)`, graphique identique, titre "Learning Curve — Classification"
- [X] T026 [US4] Ajouter Section 4 dans `notebooks/04_model_evaluation.ipynb` — cellule markdown d'analyse overfitting pour chaque modèle : écart train/validation sur la learning curve, commentaire sur la variance du modèle, conclusion explicite ("Pas de surapprentissage détecté" ou "Surapprentissage modéré observé — envisager régularisation")
- [X] T027 [US4] Ajouter Section 5 dans `notebooks/04_model_evaluation.ipynb` — cellule markdown de conclusions orientées production : forces/limites de chaque modèle, recommandation pour la mise en production (API feature 001), mention des compétences Simplon couvertes (C9, C11), vérifier Restart & Run All sans erreur

**Checkpoint** : US4 complète — notebook 04 entièrement validé (Restart & Run All sans erreur).

---

## Phase finale : Polish & conformité

- [X] T028 [P] PEP8 + black sur `ml_models/` et `business/` : `flake8 ml_models/ business/ --max-line-length=88 && black ml_models/ business/`
- [X] T029 [P] Vérifier que `classification.pkl` est bien couvert par `.gitignore` (pas de .pkl dans `git status`)
- [X] T030 [P] Vérifier `metadata.json` v1.1.0 : clés `regression.metriques_test.r2` préservées + `classification.metriques_test.accuracy` > 0.85
- [X] T031 Vérifier `Restart & Run All` final sur `notebooks/03_model_training.ipynb` complet (régression + classification) — < 5 minutes sans erreur

---

## Dépendances et ordre d'exécution

### Dépendances entre phases

- **Phase 1 (Setup)** : Aucune — démarre immédiatement.
- **US1 (Phase 3)** : Dépend de Phase 1. Démarre après T001–T003.
- **US2 (Phase 4)** : Dépend de US1 — encode les hyperparamètres optimaux de US1.
- **US3 (Phase 5)** : Dépend de US2 — predict_risk() charge classification.pkl.
- **US4 (Phase 6)** : Dépend de US1 + US2 — charge metadata.json v1.1.0 et les deux pipelines.
- **Polish** : Dépend de US1 + US2 + US3 + US4.

### Opportunités de parallélisme

- **Phase 1** : T001, T002, T003 en parallèle.
- **US3** : T016 (tests clf) ‖ T017 (tests business) ‖ T018–T019 (predict_risk) ; T020 (scoring) ‖ T021 (risk_engine) — tous fichiers distincts.
- **Polish** : T028, T029, T030 en parallèle.

---

## Exemple de parallélisme

### US3 — predict_risk() + modules métier

```bash
# Simultanément :
Task: "Créer tests/unit/test_classification.py"   # T016
Task: "Créer tests/unit/test_business.py"         # T017
Task: "Ajouter predict_risk() dans predict.py"    # T018+T019
Task: "Créer business/scoring.py"                 # T020
Task: "Créer business/risk_engine.py"             # T021
# Puis séquentiellement :
Task: "pytest -v → tous PASSED"                   # T022
```

---

## Stratégie d'implémentation

### MVP First (US1 uniquement)

1. Phase 1 (Setup)
2. US1 — section classification dans notebook 03 (T004–T010)
3. **STOP et VALIDATION** : Restart & Run All, accuracy CV > 0.85, heatmap + ROC présents
4. Démo MVP : notebook complet régression + classification prêt

### Livraison complète

1. Phase 1 → Setup OK
2. US1 → Notebook classification validé
3. US2 → Script standalone → classification.pkl + metadata.json v1.1.0
4. US3 → predict_risk() + modules métier → tests 100% PASSED
5. US4 → Notebook évaluation comparative → Restart & Run All OK
6. Polish → PEP8 + vérifications finales

---

## Notes

- `[P]` = peut s'exécuter en parallèle (fichiers distincts)
- `[USn]` = traçabilité vers la User Story dans spec.md
- `CLASSES_ORDER = ['faible', 'moyen', 'eleve', 'critique']` FIGÉ dans tous les fichiers
- `classification.pkl` JAMAIS commité (constitution Principe IV)
- `metadata.json` TOUJOURS commité (pas de données sensibles)
- La fusion de metadata.json (US2) DOIT préserver les métriques de régression existantes
- `business/scoring.py` et `business/risk_engine.py` sont des modules Python purs — zéro dépendance sklearn
