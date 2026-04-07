---

description: "Liste de tâches — Exploration des Données et Feature Engineering"
---

# Tasks: Exploration des Données et Feature Engineering

**Input**: Documents de conception dans `specs/002-exploration-feature-engineering/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Inclus — requis par la constitution (Principe V) pour les scripts Python.
Les notebooks sont validés par exécution (Restart & Run All).

**Organisation**: 3 User Stories — exploration (US1), feature engineering (US2),
scripts réutilisables (US3).

## Format: `[ID] [P?] [Story?] Description — fichier cible`

---

## Phase 1 : Setup

**But**: Créer les répertoires manquants et vérifier les prérequis.

- [x] T001 Créer le répertoire `data/processed/` (destination de `features.csv`)
- [x] T002 [P] Créer le répertoire `notebooks/` s'il n'existe pas déjà
- [x] T003 [P] Vérifier la présence et l'intégrité de `insurance.csv` à la racine du projet (assert shape == (1338, 7) et 0 valeurs nulles)

---

## Phase 2 : Fondation (Prérequis bloquants)

**But**: Scripts de transformation réutilisables — DOIVENT exister avant les notebooks
car le notebook 02 les importe.

**⚠️ CRITIQUE**: Les notebooks ne peuvent pas importer `cleaning.py` et `normalization.py`
avant que ces fichiers soient créés.

- [x] T004 Créer `data_pipeline/transform/cleaning.py` : fonction `rename_columns(df: pd.DataFrame) -> pd.DataFrame` mappant les colonnes Kaggle vers le nommage français (sex→sexe, bmi→imc, children→enfants, smoker→fumeur), avec docstring en français documentant le mapping complet
- [x] T005 [P] Créer `data_pipeline/transform/normalization.py` : fonction `encode_categoricals(df: pd.DataFrame) -> pd.DataFrame` encodant sexe ('female'→1, 'male'→0 ET 'femme'→1, 'homme'→0), fumeur ('yes'/'oui'→1, 'no'/'non'→0), region (pd.get_dummies avec drop_first=True, northeast supprimé), avec docstring en français documentant les encodages
- [x] T006 [P] Vérifier que `data_pipeline/__init__.py` et `data_pipeline/transform/__init__.py` existent pour permettre les imports Python

**Checkpoint**: `from data_pipeline.transform.cleaning import rename_columns` fonctionne sans erreur.

---

## Phase 3 : User Story 1 — Notebook d'Exploration EDA (Priority: P1) 🎯 MVP

**But**: Produire un notebook d'exploration documenté avec 8+ visualisations et
insights en markdown, exécutable de bout en bout.

**Test indépendant**: `Kernel → Restart & Run All` sur `notebooks/01_data_exploration.ipynb`
s'exécute sans erreur. Le notebook produit ≥ 8 graphiques, tous avec titre et axes
labellisés, et des cellules markdown entre chaque section.

### Tests US1

- [ ] T007 [US1] Vérifier manuellement via `Restart & Run All` que `ExplorationML.ipynb` (à la racine) s'exécute sans erreur et produit les sorties attendues (df.shape = (1338, 7), 0 valeurs nulles, ≥ 8 graphiques)

### Implémentation US1

- [x] T008 [US1] Enrichir `ExplorationML.ipynb` (racine) : ajout df_raw, df.shape, 7 visualisations manquantes avec insights markdown en français avec les sections suivantes dans l'ordre :

  **Section 1 — Import et chargement** :
  - Cellule markdown : titre du notebook et description du dataset
  - Imports : pandas, numpy, matplotlib.pyplot, seaborn, warnings
  - Chargement : `df = pd.read_csv('data/small_data/insurance.csv')`
  - Affichage : `df.head()`, `df.shape`, `df.dtypes`

  **Section 2 — Statistiques descriptives** :
  - Cellule markdown : insight sur la structure (1338 lignes, 7 colonnes, 0 null)
  - `df.info()`, `df.describe()`, `df.isnull().sum()`

  **Section 3 — Distribution de `charges` (graphique 1)** :
  - Cellule markdown : "La distribution de charges est très asymétrique (skew droit). Présence de deux populations distinctes : fumeurs et non-fumeurs."
  - `sns.histplot(df['charges'], kde=True, color='steelblue')` — titre "Distribution des charges médicales", axes "Charges (USD)" / "Fréquence"

  **Section 4 — Impact du tabagisme (graphiques 2)** :
  - Cellule markdown : "Les fumeurs ont un coût médian environ 3× supérieur aux non-fumeurs."
  - `sns.boxplot(x='smoker', y='charges', data=df, palette='Set2')` — titre "Charges médicales par statut fumeur"

  **Section 5 — Impact de la région (graphique 3)** :
  - Cellule markdown : insight sur les différences régionales
  - `sns.boxplot(x='region', y='charges', data=df, palette='Spectral')` — titre "Charges médicales par région"

  **Section 6 — Impact du sexe (graphique 4)** :
  - Cellule markdown : "La différence de charges entre hommes et femmes est faible et peu significative."
  - `sns.boxplot(x='sex', y='charges', data=df, palette='pastel')` — titre "Charges médicales par sexe"

  **Section 7 — Âge vs Charges (graphique 5)** :
  - Cellule markdown : "3 clusters visibles correspondant aux non-fumeurs (bas), fumeurs légers (moyen) et fumeurs avec IMC élevé (haut)."
  - `sns.scatterplot(x='age', y='charges', hue='smoker', data=df, palette='coolwarm', alpha=0.6)` — titre "Âge vs Charges médicales (coloré par statut fumeur)"

  **Section 8 — IMC vs Charges (graphique 6)** :
  - Cellule markdown : "Un seuil visible autour de IMC=30 : les fumeurs obèses ont des charges nettement plus élevées."
  - `sns.scatterplot(x='bmi', y='charges', hue='smoker', data=df, palette='coolwarm', alpha=0.6)` — titre "IMC vs Charges médicales (coloré par statut fumeur)"

  **Section 9 — Heatmap des corrélations (graphique 7)** :
  - Encodage temporaire pour corrélations : `df_corr = df.copy(); df_corr['smoker'] = ...; df_corr['sex'] = ...`
  - Cellule markdown : "smoker est la variable la plus corrélée à charges (≈ 0.79). age et bmi ont une corrélation modérée."
  - `sns.heatmap(df_corr[['age','sex','bmi','children','smoker','charges']].corr(), annot=True, fmt='.2f', cmap='coolwarm', square=True)` — titre "Matrice de corrélations"

  **Section 10 — Distribution de chaque variable (graphique 8)** :
  - Cellule markdown : "Vue d'ensemble des distributions — permet de détecter outliers et asymétries."
  - `fig, axes = plt.subplots(2, 4, figsize=(16, 8))` avec `sns.histplot` ou `sns.countplot` selon le type de chaque variable

  **Section 11 — Conclusions** :
  - Cellule markdown récapitulant les 5 insights principaux et leurs implications pour la modélisation

**Checkpoint**: US1 complète — notebook exécutable et documenté.

---

## Phase 4 : User Story 2 — Feature Engineering et Préparation ML (Priority: P1) 🎯 MVP

**But**: Encoder les variables, créer la target `categorie_risque`, effectuer le
split 80/20 et sauvegarder `data/processed/features.csv`.

**Test indépendant**: `Restart & Run All` sur `notebooks/02_feature_engineering.ipynb`
sans erreur. `data/processed/features.csv` créé avec 1 338 lignes, colonnes encodées,
`categorie_risque` à 4 valeurs, X_train.shape[0] ≈ 1 070.

### Tests US2

- [x] T009 [P] [US2] Créer `tests/unit/test_feature_engineering.py` : assertions sur le fichier `data/processed/features.csv` (shape, colonnes attendues, valeurs categorie_risque, 0 valeurs nulles)

### Implémentation US2

- [x] T010 [US2] Créer `notebooks/02_feature_engineering.ipynb` (lit insurance.csv à la racine) avec les sections suivantes dans l'ordre :

  **Section 1 — Import et chargement** :
  - Imports : pandas, numpy, sklearn.model_selection.train_test_split, sys, os
  - `sys.path.insert(0, os.path.abspath('..'))` pour les imports locaux
  - `from data_pipeline.transform.cleaning import rename_columns`
  - `from data_pipeline.transform.normalization import encode_categoricals`
  - Chargement : `df = pd.read_csv('data/small_data/insurance.csv')`

  **Section 2 — Renommage des colonnes** :
  - Cellule markdown : "Renommage vers le nommage métier français (constitution §2)"
  - `df = rename_columns(df)` — afficher `df.columns.tolist()`

  **Section 3 — Encodage des variables catégorielles** :
  - Cellule markdown : "Encodage : sexe (0/1), fumeur (0/1), region (one-hot, northeast supprimé)"
  - `df = encode_categoricals(df)` — afficher `df.dtypes` et `df.head()`

  **Section 4 — Création de la target `categorie_risque`** :
  - Cellule markdown : "Seuils définis dans la constitution AssuML : < 5000 → faible, 5000-15000 → moyen, 15000-30000 → eleve, ≥ 30000 → critique"
  - `df['categorie_risque'] = pd.cut(df['charges'], bins=[0, 5000, 15000, 30000, float('inf')], labels=['faible', 'moyen', 'eleve', 'critique'])`
  - Afficher `df['categorie_risque'].value_counts()` et `df['categorie_risque'].value_counts(normalize=True).round(3)`
  - Graphique : `sns.countplot(x='categorie_risque', data=df, order=['faible','moyen','eleve','critique'], palette='RdYlGn_r')` — titre "Distribution des catégories de risque"
  - Cellule markdown avec avertissement sur le déséquilibre (~7% critique)

  **Section 5 — Séparation features / targets** :
  - Cellule markdown : "X : toutes les colonnes sauf charges et categorie_risque"
  - `feature_cols = ['age', 'sexe', 'imc', 'enfants', 'fumeur', 'region_northwest', 'region_southeast', 'region_southwest']`
  - `X = df[feature_cols]`
  - `y_reg = df['charges']` (target régression)
  - `y_clf = df['categorie_risque']` (target classification)
  - Afficher `X.shape`, `X.dtypes`

  **Section 6 — Train/Test Split 80/20** :
  - Cellule markdown : "Split stratifié sur y_clf pour conserver les proportions de classes (stratify=y_clf)"
  - `X_train, X_test, y_train_reg, y_test_reg, y_train_clf, y_test_clf = train_test_split(X, y_reg, y_clf, test_size=0.2, random_state=42, stratify=y_clf)` *(NB: décomposer en 2 appels si besoin)*
  - Afficher les shapes : `X_train.shape`, `X_test.shape`
  - `assert X_train.shape[0] + X_test.shape[0] == 1338`
  - Vérifier la stratification : `y_train_clf.value_counts(normalize=True)` vs `y_test_clf.value_counts(normalize=True)`

  **Section 7 — Sauvegarde** :
  - `os.makedirs('data/processed', exist_ok=True)`
  - `df_save = X.copy(); df_save['charges'] = y_reg; df_save['categorie_risque'] = y_clf`
  - `df_save.to_csv('data/processed/features.csv', index=False)`
  - `print(f"✅ features.csv sauvegardé : {df_save.shape[0]} lignes, {df_save.shape[1]} colonnes")`
  - Afficher `df_save.head()` et `df_save.dtypes`

**Checkpoint**: US2 complète — features.csv créé, splits documentés.

---

## Phase 5 : User Story 3 — Scripts de Transformation Réutilisables (Priority: P2)

**But**: Valider que `cleaning.py` et `normalization.py` sont testés et importables
dans des contextes tiers (pipeline ETL, feature 001).

**Test indépendant**: `pytest tests/unit/test_cleaning.py tests/unit/test_normalization.py -v`
passe sans erreur. Les scripts sont importables depuis la racine du projet.

### Tests US3

- [x] T011 [P] [US3] Créer `tests/unit/test_cleaning.py` : tester `rename_columns()` sur un DataFrame de 3 lignes synthétiques — vérifier que 'sex'→'sexe', 'bmi'→'imc', 'children'→'enfants', 'smoker'→'fumeur', que 'age'/'region'/'charges' restent inchangées, et que la fonction fonctionne sur un sous-ensemble du dataset
- [x] T012 [P] [US3] Créer `tests/unit/test_normalization.py` : tester `encode_categoricals()` sur DataFrame synthétique — vérifier encodage sexe (female=1, male=0), fumeur (yes=1, no=0), one-hot region (région northeast absent, 3 colonnes binaires présentes), et que la fonction accepte les valeurs françaises (femme/homme, oui/non)

### Complétion US3

- [x] T013 [US3] Vérifier que `cleaning.py` et `normalization.py` respectent PEP8 (`flake8 data_pipeline/transform/ --max-line-length=88`) et formatter avec `black data_pipeline/transform/`

**Checkpoint**: US3 complète — scripts testés, conformes PEP8, importables.

---

## Phase finale : Polish

**But**: Validation complète et conformité.

- [x] T014 [P] Exécuter `Restart & Run All` sur les deux notebooks et corriger toute erreur résiduelle
- [x] T015 [P] Vérifier que les outputs des notebooks sont clairs (commandes `matplotlib inline` ou `%matplotlib inline` présentes, figures lisibles avec titres complets)
- [x] T016 Exécuter `pytest tests/unit/test_cleaning.py tests/unit/test_normalization.py tests/unit/test_feature_engineering.py -v` et corriger les échecs
- [x] T017 [P] Vérifier la cohérence des encodages entre le notebook 02 et `normalization.py` (mêmes mappings, mêmes seuils, même référence one-hot)

---

## Dépendances et ordre d'exécution

### Dépendances entre phases

- **Phase 1 (Setup)** : Aucune dépendance — démarre immédiatement.
- **Phase 2 (Fondation)** : Dépend de Phase 1 — BLOQUE les notebooks qui importent les scripts.
- **US1 (Phase 3)** : Dépend de Phase 2 (même si le notebook 01 n'importe pas les scripts, cohérence requise). Peut démarrer dès la Phase 1.
- **US2 (Phase 4)** : Dépend de Phase 2 (imports `cleaning.py` et `normalization.py` requis).
- **US3 (Phase 5)** : Dépend de Phase 2 (scripts déjà créés — tests de validation uniquement).
- **Polish** : Dépend de US1 + US2 + US3.

### Opportunités de parallélisme

- **Phase 2** : T004 et T005 en parallèle (fichiers distincts).
- **US3** : T011 et T012 en parallèle (fichiers distincts).
- **Polish** : T014, T015, T017 en parallèle.
- **US1 et US2** : peuvent se développer en parallèle (notebooks dans des fichiers distincts, pas de dépendance mutuelle).

---

## Exemples de parallélisme

### Phase 2 — Scripts de transformation

```bash
# Simultanément :
Task: "Créer data_pipeline/transform/cleaning.py"       # T004
Task: "Créer data_pipeline/transform/normalization.py"  # T005
```

### US3 — Tests unitaires

```bash
# Simultanément :
Task: "Créer tests/unit/test_cleaning.py"       # T011
Task: "Créer tests/unit/test_normalization.py"  # T012
```

---

## Stratégie d'implémentation

### MVP First (US1 uniquement)

1. Phase 1 (Setup) — 5 min
2. Phase 2 (Fondation — scripts) — créer les deux fichiers
3. US1 — notebook exploration complet
4. **STOP et VALIDATION** : Restart & Run All sans erreur, 8 graphiques présents
5. Démo MVP : notebook EDA documenté prêt pour la soutenance

### Livraison complète

1. Phase 1 + Phase 2 → scripts opérationnels
2. US1 (notebook 01) + US3 tests en parallèle
3. US2 (notebook 02) → features.csv généré
4. Polish → validation PEP8, tests pytest, cohérence encodages

---

## Notes

- `[P]` = peut s'exécuter en parallèle (fichiers distincts)
- `[USn]` = traçabilité vers la User Story dans spec.md
- Les notebooks DOIVENT s'exécuter sans erreur avec `Restart & Run All` (constitution Principe I)
- `features.csv` peut être commité (données non sensibles, pas de PII)
- Les fichiers `__init__.py` dans `data_pipeline/` et `data_pipeline/transform/` sont essentiels pour les imports Python depuis les notebooks
- `random_state=42` est OBLIGATOIRE sur tous les appels `train_test_split` (reproductibilité)
- La catégorie de référence one-hot est toujours `northeast` (cohérence avec feature 001)
