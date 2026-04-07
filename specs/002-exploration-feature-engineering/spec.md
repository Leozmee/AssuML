# Feature Specification: Exploration des Données et Feature Engineering

**Feature Branch**: `002-exploration-feature-engineering`
**Created**: 2026-04-07
**Status**: Draft
**Input**: Exploration complète du dataset insurance.csv (1 338 lignes),
visualisations, feature engineering, encodage, création de la target
classification, train/test split, et scripts de nettoyage/normalisation.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Exploration visuelle du dataset (Priority: P1)

Un data scientist charge le dataset brut et produit un rapport d'exploration
documenté (notebook) qui révèle la structure des données, les distributions,
les corrélations et les insights clés, afin d'orienter les choix de modélisation.

**Why this priority**: L'exploration est le prérequis absolu à tout travail ML.
Elle valide la qualité des données et justifie les choix de preprocessing.
C'est la compétence C1 (manipulation de données) de la certification.

**Independent Test**: Exécuter le notebook `01_data_exploration.ipynb` de bout
en bout (Restart & Run All) sans erreur. Vérifier la présence de : `df.head()`,
`df.info()`, `df.describe()`, `df.shape`, et au moins 8 graphiques avec
titres et axes labellisés.

**Acceptance Scenarios**:

1. **Given** le fichier `data/small_data/insurance.csv`, **When** le notebook
   est exécuté, **Then** les cellules affichent : shape (1338, 7), 0 valeur
   nulle, types corrects (int64, float64, object), et les statistiques
   descriptives (mean charges ≈ 13 270, max ≈ 63 770).
2. **Given** le dataset chargé, **When** les 8 visualisations sont générées,
   **Then** chaque graphique possède un titre, des axes labellisés, et une
   légende si plusieurs groupes sont représentés.
3. **Given** les visualisations produites, **When** un lecteur consulte le
   notebook, **Then** chaque section graphique est précédée d'une cellule
   markdown documentant l'insight observé (ex. "Les fumeurs ont un coût
   médian 3× supérieur aux non-fumeurs").
4. **Given** la heatmap de corrélations, **When** elle est affichée, **Then**
   les coefficients de corrélation sont annotés numériquement et les variables
   les plus corrélées à `charges` sont identifiables visuellement.

---

### User Story 2 — Feature Engineering et préparation ML (Priority: P1)

Un data scientist transforme les données brutes en features numériques
exploitables par les modèles ML, crée la variable cible de classification,
effectue le train/test split, et sauvegarde le dataset préparé pour
l'entraînement des modèles.

**Why this priority**: Le feature engineering est le lien entre l'exploration
et l'entraînement. Sans données encodées et splitées, les modèles ML de la
feature 001 ne peuvent pas être entraînés.

**Independent Test**: Exécuter `02_feature_engineering.ipynb` de bout en bout.
Vérifier : colonnes encodées (sexe 0/1, fumeur 0/1, region one-hot),
colonne `categorie_risque` présente avec 4 valeurs distinctes, shapes de
X_train/X_test/y_train/y_test cohérentes (80/20 sur 1 338 lignes),
fichier `data/processed/features.csv` créé.

**Acceptance Scenarios**:

1. **Given** le dataset brut chargé, **When** l'encodage est appliqué,
   **Then** les colonnes `sex` et `smoker` deviennent des entiers 0/1,
   et `region` est remplacée par 3 colonnes binaires one-hot (drop_first=True,
   northeast comme référence supprimée).
2. **Given** la colonne `charges`, **When** la target `categorie_risque` est
   créée, **Then** : charges < 5 000 → "faible", 5 000–15 000 → "moyen",
   15 000–30 000 → "eleve", ≥ 30 000 → "critique". La distribution des
   classes est affichée (graphique + tableau de comptages).
3. **Given** les features encodées et la target, **When** le split est
   effectué, **Then** X_train contient 80% des observations (≈ 1 070 lignes),
   X_test contient 20% (≈ 268 lignes), avec `random_state=42` pour la
   reproductibilité.
4. **Given** le dataset préparé, **When** il est sauvegardé, **Then** le
   fichier `data/processed/features.csv` existe, contient toutes les colonnes
   encodées + `charges` + `categorie_risque`, et peut être rechargé sans perte.

---

### User Story 3 — Scripts de nettoyage et normalisation réutilisables (Priority: P2)

Un data scientist dispose de fonctions Python encapsulant le mapping des noms
de colonnes (anglais → français) et l'encodage, réutilisables dans le pipeline
ETL de production (feature 001).

**Why this priority**: Ces scripts évitent la duplication entre le notebook
et le pipeline ETL. Ils garantissent que la même logique de transformation
est appliquée en exploration et en production.

**Independent Test**: Importer `cleaning.py` et `normalization.py`, appeler
`rename_columns(df)` sur le dataset brut → vérifier que `sex` devient `sexe`,
`bmi` devient `imc`, etc. Appeler `encode_categoricals(df)` → vérifier
l'encodage numérique des colonnes.

**Acceptance Scenarios**:

1. **Given** un DataFrame avec les colonnes originales (age, sex, bmi,
   children, smoker, region, charges), **When** `rename_columns(df)` est
   appelé, **Then** le DataFrame retourné contient les colonnes : age, sexe,
   imc, enfants, fumeur, region, charges (mapping exact du dataset Kaggle vers
   nommage métier français).
2. **Given** un DataFrame avec nommage français, **When** `encode_categoricals(df)`
   est appelé, **Then** `sexe` est 0/1 (femme=1, homme=0), `fumeur` est 0/1
   (oui=1, non=0), `region` est one-hot avec drop_first=True.
3. **Given** les deux fonctions, **When** elles sont importées dans un script
   ou notebook tiers, **Then** elles s'exécutent sans erreur et retournent
   un DataFrame Pandas bien formé.

---

### Edge Cases

- Si le fichier `data/small_data/insurance.csv` est absent, le notebook DOIT
  afficher un message d'erreur explicite (FileNotFoundError avec chemin attendu).
- Si une valeur de `charges` tombe exactement sur un seuil (5 000, 15 000,
  30 000), la catégorie assignée DOIT être cohérente et documentée (seuil
  inférieur inclus : `< 5 000` → faible, `≥ 5 000` → moyen, etc.).
- La colonne `region` one-hot DOIT toujours supprimer la même catégorie
  de référence (northeast) pour garantir la reproductibilité.
- Les scripts `cleaning.py` et `normalization.py` DOIVENT fonctionner sur un
  sous-ensemble du dataset (pas seulement sur les 1 338 lignes complètes).

---

## Requirements *(mandatory)*

### Functional Requirements

**Notebook Exploration (01)**
- **FR-001**: Le notebook DOIT charger `data/small_data/insurance.csv` et
  afficher `df.head()`, `df.info()`, `df.describe()`, `df.shape`.
- **FR-002**: Le notebook DOIT produire au moins 8 visualisations :
  histogramme de `charges`, boxplot `charges` par `smoker`, boxplot `charges`
  par `region`, boxplot `charges` par `sex`, scatter `age` vs `charges` coloré
  par `smoker`, scatter `bmi` vs `charges` coloré par `smoker`, heatmap des
  corrélations (annotée), distribution de chaque variable (histogrammes ou
  countplots selon le type).
- **FR-003**: Chaque graphique DOIT avoir un titre et des axes labellisés.
  Les graphiques avec plusieurs groupes DOIVENT avoir une légende.
- **FR-004**: Chaque section de visualisation DOIT être précédée d'une cellule
  markdown documentant l'insight principal observé.
- **FR-005**: Le notebook DOIT s'exécuter de bout en bout sans erreur
  (Restart & Run All).

**Notebook Feature Engineering (02)**
- **FR-006**: Le notebook DOIT encoder `sex` en 0/1 (femme=1, homme=0) et
  `smoker` en 0/1 (yes=1, no=0).
- **FR-007**: Le notebook DOIT encoder `region` en one-hot avec
  `drop_first=True` (northeast comme référence supprimée).
- **FR-008**: Le notebook DOIT créer la colonne `categorie_risque` depuis
  `charges` avec les seuils : < 5 000 → "faible", 5 000–15 000 → "moyen",
  15 000–30 000 → "eleve", ≥ 30 000 → "critique".
- **FR-009**: Le notebook DOIT afficher la distribution des classes
  `categorie_risque` (comptage et pourcentage).
- **FR-010**: Le notebook DOIT effectuer un train/test split 80/20 avec
  `random_state=42` sur les features X et les deux targets (y_regression=charges,
  y_classification=categorie_risque).
- **FR-011**: Le notebook DOIT sauvegarder le dataset préparé dans
  `data/processed/features.csv` (toutes colonnes encodées + charges + categorie_risque).
- **FR-012**: Le notebook DOIT s'exécuter de bout en bout sans erreur.

**Scripts de transformation**
- **FR-013**: `data_pipeline/transform/cleaning.py` DOIT implémenter
  `rename_columns(df: pd.DataFrame) → pd.DataFrame` mappant les colonnes
  Kaggle vers le nommage français (sex→sexe, bmi→imc, children→enfants,
  smoker→fumeur).
- **FR-014**: `data_pipeline/transform/normalization.py` DOIT implémenter
  `encode_categoricals(df: pd.DataFrame) → pd.DataFrame` appliquant
  l'encodage 0/1 et one-hot défini dans le notebook 02.
- **FR-015**: Les deux fonctions DOIVENT avoir des docstrings en français
  documentant les paramètres, le retour et les transformations effectuées.

### Key Entities

- **Dataset brut** : `insurance.csv` — 1 338 lignes, colonnes originales Kaggle
  (age, sex, bmi, children, smoker, region, charges).
- **Dataset préparé** : `features.csv` — colonnes encodées, `categorie_risque`
  ajoutée, prêt pour l'entraînement ML.
- **Splits d'entraînement** : X_train, X_test, y_train_reg, y_test_reg (charges),
  y_train_clf, y_test_clf (categorie_risque) — générés avec random_state=42.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les deux notebooks s'exécutent de bout en bout (Restart & Run All)
  sans erreur en moins de 2 minutes chacun.
- **SC-002**: Le notebook 01 produit exactement ≥ 8 graphiques, tous avec titre
  et axes labellisés.
- **SC-003**: Le fichier `data/processed/features.csv` est créé et contient
  1 338 lignes et le bon nombre de colonnes (features encodées + charges +
  categorie_risque).
- **SC-004**: La distribution des classes `categorie_risque` est documentée et
  ne contient aucune valeur nulle ni classe non prévue.
- **SC-005**: Les fonctions `rename_columns()` et `encode_categoricals()` sont
  importables et utilisables dans un script tiers sans modification.
- **SC-006**: X_train contient 80% des données (≈ 1 070 lignes) et X_test
  contient 20% (≈ 268 lignes) — vérifiable par `assert`.

---

## Assumptions

- Le fichier `data/small_data/insurance.csv` est présent et intact (1 338 lignes,
  7 colonnes : age, sex, bmi, children, smoker, region, charges).
- La bibliothèque de visualisation utilisée est `matplotlib` + `seaborn`
  (standard pour notebooks EDA).
- L'encodage one-hot de `region` supprime toujours `northeast` (drop_first=True
  avec ordre alphabétique pandas : northeast, northwest, southeast, southwest
  → northeast supprimé).
- Le split 80/20 est fixe (`random_state=42`) pour garantir la reproductibilité
  entre exécutions.
- Le répertoire `data/processed/` est créé automatiquement par le notebook si
  absent.
- Les scripts `cleaning.py` et `normalization.py` opèrent sur des DataFrames
  Pandas en mémoire — ils ne lisent ni n'écrivent de fichiers directement.
- Les notebooks sont exécutés dans un environnement Python avec toutes les
  dépendances de `requirements.txt` installées.
