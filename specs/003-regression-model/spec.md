# Feature Specification: Modèle de Régression — Prédiction du Coût Médical

**Feature Branch**: `003-regression-model`
**Created**: 2026-05-04
**Status**: Draft
**Input**: Entraîner un modèle de régression pour prédire le coût médical annuel (variable `charges`). Comparer 3 algorithmes, optimiser le meilleur, sauvegarder un pipeline complet, et exposer une fonction de prédiction. Objectif R² > 0.80.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Comparaison d'algorithmes de régression (Priority: P1)

Un data scientist entraîne et compare trois algorithmes de régression (régression linéaire, forêt aléatoire, gradient boosting) sur le dataset d'assurance, évalue chacun avec des métriques standards (R², MAE, RMSE), et identifie le meilleur modèle candidat pour l'optimisation.

**Why this priority**: C'est le point de départ de tout le pipeline ML. Sans comparaison rigoureuse, le choix du modèle final n'est pas justifié. Cette étape valide aussi la qualité du dataset préparé par la feature 002.

**Independent Test**: Exécuter `notebooks/03_model_training.ipynb` (Restart & Run All). Vérifier la présence d'un tableau de comparaison avec R², MAE, RMSE pour les 3 algorithmes, et l'identification explicite du meilleur modèle dans une cellule markdown.

**Acceptance Scenarios**:

1. **Given** le fichier `data/processed/features.csv` chargé (1 338 lignes, colonnes encodées), **When** les 3 modèles sont entraînés sur le split 80/20, **Then** chaque modèle produit un score R², un MAE et un RMSE calculés sur le jeu de test.
2. **Given** les 3 modèles entraînés, **When** les métriques sont affichées, **Then** un tableau comparatif est présent avec les 3 algorithmes en ligne et R²/MAE/RMSE en colonnes, trié par R² décroissant.
3. **Given** le tableau comparatif, **When** le meilleur modèle est identifié, **Then** une cellule markdown documente explicitement le choix avec justification chiffrée (ex. "GradientBoostingRegressor retenu : R²=0.87, MAE=2 450 USD").
4. **Given** les prédictions du meilleur modèle sur le test set, **When** les visualisations sont générées, **Then** un scatter plot "prédictions vs valeurs réelles" et un graphique de résidus sont présents, avec titres et axes labellisés.

---

### User Story 2 — Optimisation et validation approfondie du meilleur modèle (Priority: P1)

Un data scientist optimise les hyperparamètres du meilleur modèle sélectionné via une recherche sur grille, valide sa robustesse par cross-validation 5 plis, et analyse la contribution de chaque variable d'entrée à la prédiction.

**Why this priority**: L'optimisation est nécessaire pour atteindre l'objectif R² > 0.80. La cross-validation garantit que la performance n'est pas due au hasard du split. La feature importance oriente les futurs travaux de feature engineering.

**Independent Test**: Dans `notebooks/03_model_training.ipynb`, vérifier la présence d'un bloc GridSearchCV avec au moins 4 hyperparamètres explorés, un score cross-validation 5-fold affiché (moyenne ± écart-type), et un graphique de feature importance.

**Acceptance Scenarios**:

1. **Given** le meilleur algorithme identifié à l'US1, **When** GridSearchCV est exécuté avec la grille définie (n_estimators, max_depth, min_samples_split, min_samples_leaf), **Then** les meilleurs hyperparamètres sont affichés et le modèle optimisé est instancié avec ces paramètres.
2. **Given** le modèle optimisé, **When** la cross-validation 5 plis est réalisée sur l'ensemble complet (train + test), **Then** les 5 scores R² individuels et leur moyenne ± écart-type sont affichés.
3. **Given** la cross-validation terminée, **When** le score moyen est calculé, **Then** le R² moyen sur 5 plis est supérieur à 0.80.
4. **Given** le modèle final entraîné, **When** la feature importance est calculée, **Then** un graphique horizontal trié par importance décroissante affiche la contribution de chaque variable, avec une cellule markdown identifiant les 3 variables les plus influentes.

---

### User Story 3 — Script d'entraînement standalone et sauvegarde du pipeline (Priority: P1)

Un data scientist (ou un système CI/CD) peut entraîner et sauvegarder le modèle de régression complet en exécutant un script Python autonome, sans passer par le notebook. Le modèle sauvegardé embarque tout le preprocessing nécessaire pour être utilisable directement en production.

**Why this priority**: Le notebook est un outil d'exploration, pas de production. Le script standalone est le livrable réutilisable par la feature 001 (API FastAPI). Un pipeline complet (preprocessing + modèle) garantit la cohérence entre entraînement et inférence.

**Independent Test**: Exécuter `python ml_models/training/train_regression.py` depuis la racine du projet. Vérifier que `ml_models/saved_models/regression.pkl` est créé, que le script affiche les métriques finales, et que le fichier `.pkl` est chargeable avec `joblib.load()`.

**Acceptance Scenarios**:

1. **Given** la présence de `data/processed/features.csv`, **When** le script `train_regression.py` est exécuté, **Then** le script s'exécute sans erreur et affiche les métriques finales (R², MAE, RMSE) sur le jeu de test.
2. **Given** l'exécution réussie du script, **When** le fichier `ml_models/saved_models/regression.pkl` est chargé, **Then** l'objet chargé est un Pipeline scikit-learn contenant à la fois le preprocessing (ColumnTransformer avec StandardScaler) et le modèle de régression.
3. **Given** le pipeline chargé, **When** il reçoit des données brutes au format attendu, **Then** il retourne une prédiction de coût en USD sans nécessiter de preprocessing externe.
4. **Given** le répertoire `ml_models/saved_models/` absent, **When** le script est exécuté, **Then** le répertoire est créé automatiquement avant la sauvegarde.

---

### User Story 4 — Fonction de prédiction utilisable en production (Priority: P2)

Un développeur ou un système appelant peut prédire le coût médical annuel d'un profil assuré en appelant une fonction Python unique avec les caractéristiques du profil, sans connaître les détails du modèle ni du preprocessing.

**Why this priority**: C'est l'interface que la feature 001 (API FastAPI) consommera directement. Sans cette fonction, le modèle n'est pas intégrable dans le système de souscription. P2 car elle dépend de l'US3 (pipeline sauvegardé).

**Independent Test**: Depuis un script Python quelconque, importer `from ml_models.prediction.predict import predict_cost` et appeler `predict_cost(age=45, sexe=1, imc=32.0, enfants=2, fumeur=1, region='southeast')`. Vérifier que la valeur retournée est un float positif dans une plage réaliste (1 000–65 000 USD).

**Acceptance Scenarios**:

1. **Given** le fichier `regression.pkl` présent dans `ml_models/saved_models/`, **When** `predict_cost(age, sexe, imc, enfants, fumeur, region)` est appelé avec des valeurs valides, **Then** la fonction retourne un float représentant le coût prédit en USD.
2. **Given** un profil fumeur typique (fumeur=1, imc=32, age=45), **When** `predict_cost()` est appelé, **Then** la prédiction est supérieure à la prédiction du même profil non-fumeur (fumeur=0), conformément aux patterns observés en exploration.
3. **Given** le modèle chargé une fois au démarrage du module, **When** `predict_cost()` est appelé plusieurs fois, **Then** le modèle n'est pas rechargé à chaque appel (chargement singleton au niveau module).
4. **Given** le fichier `.pkl` absent, **When** `predict_cost()` est appelé, **Then** une exception explicite est levée avec le chemin attendu du fichier manquant.

---

### Edge Cases

- Si `data/processed/features.csv` est absent au lancement du script, le script DOIT lever un `FileNotFoundError` avec le chemin attendu.
- Si GridSearchCV trouve plusieurs combinaisons d'hyperparamètres avec des scores identiques, le premier résultat est retenu (comportement sklearn par défaut — documenté dans le notebook).
- La variable `region` dans `predict_cost()` accepte les valeurs anglaises originales du dataset (`northeast`, `northwest`, `southeast`, `southwest`) — le pipeline gère l'encodage.
- Les valeurs aberrantes en entrée de `predict_cost()` (IMC=0, âge négatif) ne sont pas validées dans cette feature — la validation métier est déléguée à la feature 001 (API).
- Le fichier `regression.pkl` ne doit pas être commité dans git (`.gitignore` existant).

---

## Requirements *(mandatory)*

### Functional Requirements

**Notebook d'entraînement (03)**
- **FR-001**: Le notebook DOIT charger `data/processed/features.csv`, séparer features (X) et target (`charges`), et effectuer un train/test split 80/20 avec `random_state=42`.
- **FR-002**: Le notebook DOIT entraîner LinearRegression, RandomForestRegressor et GradientBoostingRegressor, et calculer R², MAE, RMSE pour chacun sur le jeu de test.
- **FR-003**: Le notebook DOIT afficher un tableau comparatif des 3 modèles trié par R² décroissant et identifier le meilleur dans une cellule markdown justifiée.
- **FR-004**: Le notebook DOIT produire un scatter plot "prédictions vs valeurs réelles" et un graphique de résidus pour le meilleur modèle, avec titres et axes labellisés.
- **FR-005**: Le notebook DOIT exécuter GridSearchCV sur le meilleur modèle en explorant au moins 4 hyperparamètres (n_estimators, max_depth, min_samples_split, min_samples_leaf).
- **FR-006**: Le notebook DOIT réaliser une cross-validation 5 plis sur le modèle optimisé et afficher les 5 scores R² individuels + moyenne ± écart-type.
- **FR-007**: Le notebook DOIT produire un graphique de feature importance horizontal trié par importance décroissante, avec toutes les variables d'entrée.
- **FR-008**: Le notebook DOIT s'exécuter de bout en bout sans erreur (Restart & Run All).

**Script d'entraînement standalone**
- **FR-009**: `ml_models/training/train_regression.py` DOIT s'exécuter de manière autonome depuis la racine du projet (`python ml_models/training/train_regression.py`).
- **FR-010**: Le script DOIT construire un Pipeline scikit-learn combinant preprocessing (ColumnTransformer avec StandardScaler pour les numériques) et le meilleur modèle de régression optimisé.
- **FR-011**: Le script DOIT sauvegarder le pipeline dans `ml_models/saved_models/regression.pkl` (création automatique du répertoire si absent).
- **FR-012**: Le script DOIT afficher les métriques finales (R², MAE, RMSE) sur le jeu de test avant la sauvegarde.
- **FR-013**: Le script DOIT avoir une docstring en français documentant son usage et les fichiers produits.

**Fonction de prédiction**
- **FR-014**: `ml_models/prediction/predict.py` DOIT implémenter `predict_cost(age: int, sexe: int, imc: float, enfants: int, fumeur: int, region: str) -> float`.
- **FR-015**: La fonction DOIT charger `regression.pkl` une seule fois au niveau module (singleton) et non à chaque appel.
- **FR-016**: La fonction DOIT lever une exception explicite si `regression.pkl` est absent, avec le chemin attendu dans le message d'erreur.
- **FR-017**: La fonction DOIT avoir une docstring en français documentant les paramètres, le retour et les valeurs attendues pour chaque argument.

### Key Entities

- **Pipeline ML** : Objet sklearn encapsulant preprocessing + modèle de régression, sérialisé dans `regression.pkl`. Entrée : profil assuré brut. Sortie : coût prédit en USD.
- **Dataset d'entraînement** : `data/processed/features.csv` — 1 338 lignes, colonnes encodées + `charges` (target). Produit par la feature 002.
- **Splits** : X_train (≈ 1 070 lignes), X_test (≈ 268 lignes) avec `random_state=42` pour la reproductibilité.
- **Métriques de performance** : R² (variance expliquée), MAE (erreur absolue moyenne en USD), RMSE (erreur quadratique moyenne en USD).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Le notebook s'exécute de bout en bout (Restart & Run All) sans erreur en moins de 5 minutes.
- **SC-002**: Le modèle optimisé atteint un R² > 0.80 sur le jeu de test (20% des données).
- **SC-003**: Le R² moyen sur les 5 plis de cross-validation est supérieur à 0.80 (robustesse confirmée).
- **SC-004**: Le script standalone s'exécute et produit `regression.pkl` en moins de 3 minutes.
- **SC-005**: `predict_cost()` peut être importée et appelée depuis un script tiers sans modification, et retourne un float en moins de 100 ms.
- **SC-006**: Le notebook produit au minimum 4 graphiques (scatter prédictions vs réelles, résidus, feature importance, et au moins 1 graphique de comparaison des modèles).

---

## Assumptions

- Le fichier `data/processed/features.csv` est présent et intact — produit par la feature 002 avec les colonnes : `age`, `sexe`, `imc`, `enfants`, `fumeur`, `region_northwest`, `region_southeast`, `region_southwest`, `charges`, `categorie_risque`.
- La target de régression est la colonne `charges` (coût médical annuel en USD).
- Les features d'entrée du modèle sont : `age`, `sexe`, `imc`, `enfants`, `fumeur`, `region_northwest`, `region_southeast`, `region_southwest` (8 colonnes — l'encodage one-hot est déjà appliqué dans features.csv).
- Le meilleur algorithme sera vraisemblablement GradientBoostingRegressor ou RandomForestRegressor — la comparaison le confirme empiriquement.
- Le preprocessing dans le Pipeline applique StandardScaler sur les variables numériques continues ; l'encodage catégoriel est déjà réalisé en amont dans features.csv.
- `random_state=42` est utilisé sur tous les appels stochastiques (train_test_split, modèles, GridSearchCV) pour la reproductibilité.
- Les bibliothèques scikit-learn, pandas, numpy, joblib, matplotlib, seaborn sont installées dans l'environnement Python du projet.
- Le fichier `regression.pkl` n'est pas commité (déjà dans `.gitignore`).
- La fonction `predict_cost()` prend `region` comme string (`northeast`, `northwest`, `southeast`, `southwest`) — le pipeline gère la transformation en colonnes one-hot.