# Feature Specification: Modèle de Classification — Niveau de Risque Assuré

**Feature Branch**: `004-classification-risk`
**Created**: 2026-05-04
**Status**: Draft
**Input**: Entraîner un modèle de classification pour prédire `categorie_risque` (faible, moyen, eleve, critique), comparer deux algorithmes, optimiser, sauvegarder un pipeline complet, exposer `predict_risk()`, créer les modules métier `scoring.py` et `risk_engine.py`, et produire un notebook d'évaluation comparative régression + classification.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Comparaison et optimisation du modèle de classification (Priority: P1)

Un data scientist entraîne et compare RandomForestClassifier et GradientBoostingClassifier pour prédire la catégorie de risque d'un assuré (faible / moyen / élevé / critique). Il évalue chaque modèle avec les métriques multiclasses standards, optimise le meilleur via recherche sur grille, valide par cross-validation, et analyse la contribution de chaque variable.

**Why this priority**: C'est le cœur de la feature. Sans ce modèle opérationnel, ni `predict_risk()`, ni les règles de décision métier ne peuvent être démontrés. La constitution exige explicitement la classification comme second modèle ML.

**Independent Test**: Exécuter `notebooks/03_model_training.ipynb` section classification (Restart & Run All). Vérifier : rapport de classification avec accuracy > 0.85, matrice de confusion en heatmap, courbes ROC avec AUC par classe, score CV moyen > 0.85.

**Acceptance Scenarios**:

1. **Given** `data/processed/features.csv` chargé (1 338 lignes), **When** RandomForestClassifier et GradientBoostingClassifier sont entraînés sur le split 80/20, **Then** chaque modèle produit accuracy, precision, recall et f1-score (macro et par classe) calculés sur le test set.
2. **Given** les deux modèles comparés, **When** le meilleur est sélectionné, **Then** une cellule markdown justifie le choix avec les métriques chiffrées, et GridSearchCV est appliqué sur au moins 3 hyperparamètres.
3. **Given** le modèle optimisé, **When** la cross-validation 5 plis est exécutée, **Then** l'accuracy moyenne sur 5 plis est supérieure à 0.85.
4. **Given** les prédictions sur le test set, **When** la matrice de confusion est affichée, **Then** elle apparaît sous forme de heatmap annotée avec les 4 classes en lignes et colonnes (faible, moyen, eleve, critique).
5. **Given** le modèle final, **When** les courbes ROC sont tracées, **Then** une courbe ROC par classe est affichée (stratégie one-vs-rest) avec l'AUC correspondant, et une courbe macro-average est incluse.

---

### User Story 2 — Script standalone et sauvegarde du pipeline de classification (Priority: P1)

Un data scientist peut entraîner et sauvegarder le modèle de classification complet via un script Python autonome. Le pipeline sauvegardé embarque preprocessing et modèle. Les métadonnées des deux modèles (régression + classification) sont consolidées dans un seul fichier de traçabilité.

**Why this priority**: Le script est le livrable réutilisable par la feature 001 (API FastAPI). La mise à jour de `metadata.json` avec les deux modèles est requise par la constitution (Principe II) pour le module Monitoring.

**Independent Test**: Exécuter `python -m ml_models.training.train_classification`. Vérifier que `classification.pkl` est créé, que `metadata.json` contient les scores des deux modèles (régression et classification), et que le pipeline est chargeable.

**Acceptance Scenarios**:

1. **Given** `data/processed/features.csv` présent, **When** `train_classification.py` est exécuté, **Then** le script s'exécute sans erreur, affiche accuracy/precision/recall/f1 sur le test set, et crée `classification.pkl`.
2. **Given** l'exécution réussie, **When** `classification.pkl` est chargé, **Then** l'objet est un Pipeline scikit-learn avec le même ColumnTransformer que le modèle de régression (StandardScaler sur age/imc/enfants, passthrough sur le reste).
3. **Given** les deux modèles entraînés, **When** `metadata.json` est lu, **Then** il contient les sections `regression` et `classification` avec leurs métriques respectives, version, date et hyperparamètres.
4. **Given** le répertoire `ml_models/saved_models/` absent, **When** le script est exécuté, **Then** le répertoire est créé automatiquement.

---

### User Story 3 — Fonction predict_risk() et modules métier (Priority: P1)

Un développeur peut obtenir la catégorie de risque et le score de confiance d'un profil assuré via `predict_risk()`, calculer la prime d'assurance via `calculer_prime()`, et obtenir la décision de souscription (accepter / examiner / refuser) via `get_decision()`.

**Why this priority**: Ces trois fonctions forment l'interface complète que l'API FastAPI consommera (feature 001). Sans elles, le système de souscription ne peut pas être démo. La constitution définit explicitement la logique de décision dans `business/`.

**Independent Test**: Importer et appeler `predict_risk(age=45, sexe=1, imc=32.0, enfants=2, fumeur=1, region='southeast')` → retourne `('eleve', float)`. Appeler `calculer_prime(20000.0, 0.8)` → retourne float. Appeler `get_decision('critique')` → retourne `'refuser'`.

**Acceptance Scenarios**:

1. **Given** `classification.pkl` présent, **When** `predict_risk(age, sexe, imc, enfants, fumeur, region)` est appelé, **Then** la fonction retourne un tuple `(categorie_risque: str, score_risque: float)` où `categorie_risque` est l'une des 4 valeurs et `score_risque` est la probabilité maximale entre 0 et 1.
2. **Given** un profil fumeur avec IMC élevé, **When** `predict_risk()` est appelé, **Then** la catégorie retournée est `'eleve'` ou `'critique'` (cohérent avec les patterns du dataset).
3. **Given** un `cout_predit` et un `score_risque`, **When** `calculer_prime(cout_predit, score_risque)` est appelé, **Then** la prime retournée est un float supérieur à `cout_predit` (le score de risque applique un coefficient ≥ 1.0).
4. **Given** chacune des 4 catégories de risque, **When** `get_decision(categorie_risque)` est appelé, **Then** : `'faible'` → `'accepter'`, `'moyen'` → `'accepter'`, `'eleve'` → `'examiner'`, `'critique'` → `'refuser'`.

---

### User Story 4 — Notebook d'évaluation comparative des deux modèles (Priority: P2)

Un data scientist dispose d'un notebook dédié à l'évaluation comparative du modèle de régression et du modèle de classification : tableau récapitulatif des performances, courbes d'apprentissage, analyse du surapprentissage, et conclusions orientées production.

**Why this priority**: Ce notebook est le document de référence pour la soutenance. Il prouve la rigueur de l'évaluation ML et couvre les compétences C9 (traçabilité) et C11 (validation). P2 car les modèles doivent exister (US1/US2) avant l'évaluation comparative.

**Independent Test**: Exécuter `notebooks/04_model_evaluation.ipynb` (Restart & Run All) sans erreur. Vérifier : tableau récapitulatif des deux modèles, au moins 2 learning curves, section markdown d'analyse overfitting, conclusions documentées.

**Acceptance Scenarios**:

1. **Given** les deux modèles entraînés et sauvegardés, **When** le notebook est exécuté, **Then** un tableau récapitulatif côte-à-côte affiche les métriques clés de la régression (R², MAE) et de la classification (accuracy, F1-macro).
2. **Given** le notebook exécuté, **When** les learning curves sont affichées, **Then** deux graphiques sont présents (un par modèle) montrant les scores train et validation en fonction de la taille d'entraînement.
3. **Given** les learning curves, **When** l'analyse overfitting est documentée, **Then** une cellule markdown conclut explicitement sur la présence ou l'absence de surapprentissage pour chaque modèle.
4. **Given** les deux notebooks (03 et 04) exécutés, **When** un lecteur consulte le notebook 04, **Then** il peut comprendre sans contexte additionnel pourquoi les modèles retenus sont appropriés pour la production.

---

### Edge Cases

- Si `data/processed/features.csv` est absent, `train_classification.py` DOIT lever un `FileNotFoundError` avec le chemin attendu.
- La colonne `categorie_risque` contient des valeurs catégorielles string — elle DOIT être convertie en labels encodés avant l'entraînement (LabelEncoder ou équivalent, avec ordre fixe : faible, moyen, eleve, critique).
- La classe `critique` est minoritaire (~7% des données) : le rapport de classification DOIT afficher les métriques par classe pour détecter un éventuel biais sur les classes rares.
- `predict_risk()` DOIT lever `FileNotFoundError` si `classification.pkl` est absent, avec le chemin attendu.
- `calculer_prime()` DOIT retourner un float strictement positif même si `cout_predit` est proche de 0.
- `get_decision()` DOIT lever une `ValueError` explicite si la catégorie passée n'est pas l'une des 4 valeurs attendues.
- La mise à jour de `metadata.json` DOIT préserver les métriques du modèle de régression existant (fusion, pas écrasement).

---

## Requirements *(mandatory)*

### Functional Requirements

**Notebook de classification (03 — nouvelle section)**
- **FR-001**: Le notebook DOIT entraîner RandomForestClassifier et GradientBoostingClassifier sur le split 80/20 avec `random_state=42`.
- **FR-002**: Le notebook DOIT calculer et afficher accuracy, precision, recall, f1-score (macro + par classe) pour les deux modèles via `classification_report`.
- **FR-003**: Le notebook DOIT afficher la matrice de confusion du meilleur modèle en heatmap annotée (4×4, labels : faible/moyen/eleve/critique).
- **FR-004**: Le notebook DOIT tracer les courbes ROC one-vs-rest avec AUC pour chaque classe + macro-average du meilleur modèle.
- **FR-005**: Le notebook DOIT exécuter GridSearchCV sur le meilleur modèle (minimum : n_estimators, max_depth, min_samples_split).
- **FR-006**: Le notebook DOIT réaliser une cross-validation 5 plis sur l'accuracy du modèle optimisé et afficher moyenne ± écart-type.
- **FR-007**: Le notebook DOIT produire un graphique de feature importance du meilleur modèle de classification.
- **FR-008**: Le notebook DOIT s'exécuter de bout en bout sans erreur.

**Script d'entraînement standalone**
- **FR-009**: `ml_models/training/train_classification.py` DOIT s'exécuter avec `python -m ml_models.training.train_classification` depuis la racine du projet.
- **FR-010**: Le script DOIT construire un Pipeline avec le même ColumnTransformer que la régression (StandardScaler sur age/imc/enfants, passthrough sur les 5 colonnes binaires/one-hot).
- **FR-011**: Le script DOIT sauvegarder le pipeline dans `ml_models/saved_models/classification.pkl`.
- **FR-012**: Le script DOIT mettre à jour `ml_models/saved_models/metadata.json` en fusionnant les métriques de classification avec les métriques de régression existantes (version incrémentée à `1.1.0`).
- **FR-013**: Le script DOIT avoir une docstring en français documentant son usage.

**Fonctions de prédiction et métier**
- **FR-014**: `predict_risk(age, sexe, imc, enfants, fumeur, region) -> tuple[str, float]` DOIT être ajoutée dans `ml_models/prediction/predict.py`, avec chargement singleton de `classification.pkl`.
- **FR-015**: `business/scoring.py` DOIT implémenter `calculer_prime(cout_predit: float, score_risque: float) -> float` avec les coefficients : faible=1.0, moyen=1.15, eleve=1.35, critique=1.60 (coefficient sélectionné selon la catégorie issue de `predict_risk()`).
- **FR-016**: `business/risk_engine.py` DOIT implémenter `get_categorie_risque(cout_predit: float) -> str` (seuils : <5000→faible, 5000–15000→moyen, 15000–30000→eleve, ≥30000→critique) ET `get_decision(categorie_risque: str) -> str` (faible/moyen→accepter, eleve→examiner, critique→refuser).
- **FR-017**: Toutes les fonctions DOIVENT avoir des docstrings en français avec paramètres, retour et valeurs attendues.

**Notebook d'évaluation comparative (04)**
- **FR-018**: `notebooks/04_model_evaluation.ipynb` DOIT charger `metadata.json` et afficher un tableau récapitulatif côte-à-côte des deux modèles.
- **FR-019**: Le notebook DOIT produire les learning curves des deux modèles (score train vs validation en fonction de la taille d'entraînement).
- **FR-020**: Le notebook DOIT inclure une section markdown d'analyse overfitting pour chaque modèle.
- **FR-021**: Le notebook DOIT s'exécuter de bout en bout sans erreur.

### Key Entities

- **Pipeline de classification** : Pipeline sklearn (ColumnTransformer + classificateur), sérialisé dans `classification.pkl`. Entrée : 8 features encodées. Sortie : catégorie de risque (str) + score de confiance (float).
- **Catégorie de risque** : variable cible à 4 classes ordinales (`faible` < `moyen` < `eleve` < `critique`), dérivée de `charges` par la feature 002.
- **metadata.json** : fichier de traçabilité consolidé contenant les métriques des deux modèles, version `1.1.0`.
- **Prime d'assurance** : float calculé par `calculer_prime()` à partir du coût prédit et du coefficient de risque associé à la catégorie.
- **Décision de souscription** : string (`accepter`, `examiner`, `refuser`) produit par `get_decision()` selon la catégorie de risque.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Le notebook de classification s'exécute de bout en bout (Restart & Run All) sans erreur en moins de 5 minutes.
- **SC-002**: Le modèle optimisé atteint une accuracy > 0.85 sur le jeu de test (20% des données).
- **SC-003**: L'accuracy moyenne sur les 5 plis de cross-validation est supérieure à 0.85.
- **SC-004**: `train_classification.py` s'exécute et produit `classification.pkl` en moins de 3 minutes.
- **SC-005**: `predict_risk()` retourne un tuple `(str, float)` valide en moins de 100 ms.
- **SC-006**: `get_decision()` retourne la bonne décision pour les 4 catégories sans erreur.
- **SC-007**: `metadata.json` contient les métriques des deux modèles (régression ET classification) après exécution de `train_classification.py`.
- **SC-008**: Le notebook 04 s'exécute sans erreur et produit au minimum 2 learning curves et 1 tableau comparatif.

---

## Assumptions

- `data/processed/features.csv` est présent avec les colonnes : `age`, `sexe`, `imc`, `enfants`, `fumeur`, `region_northwest`, `region_southeast`, `region_southwest`, `charges`, `categorie_risque`.
- `ml_models/saved_models/regression.pkl` et `metadata.json` (version 1.0.0) existent déjà — produits par la feature 003.
- La colonne `categorie_risque` contient les valeurs string `'faible'`, `'moyen'`, `'eleve'`, `'critique'` (type Categorical ou object après chargement CSV).
- Le même ColumnTransformer que la régression est utilisé (StandardScaler sur age/imc/enfants, passthrough sur les 5 autres) pour garantir la cohérence des pipelines.
- Le split 80/20 avec `random_state=42` est identique à celui de la régression pour permettre la comparaison sur le même test set.
- `calculer_prime()` reçoit le coût prédit par `predict_cost()` et la catégorie issue de `predict_risk()` — les coefficients (1.0/1.15/1.35/1.60) sont définis dans la constitution AssuML.
- `classification.pkl` est exclu du git (`.gitignore` existant couvre `*.pkl`).
- Les `__init__.py` dans `business/` sont créés si absents.
- La courbe ROC est tracée en stratégie one-vs-rest (OvR), ce qui est standard pour la classification multiclasse avec scikit-learn (`roc_curve` + `label_binarize`).
