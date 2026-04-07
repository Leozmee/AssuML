# Research: Exploration et Feature Engineering — Décisions Techniques

**Feature**: 002-exploration-feature-engineering
**Date**: 2026-04-07
**Statut**: Complet — aucun NEEDS CLARIFICATION résiduel

---

## 1. Bibliothèque de visualisation

**Decision**: Seaborn + Matplotlib pour le notebook 01 (EDA).

**Rationale**: Seaborn est la bibliothèque de référence pour l'EDA statistique
en Python. Elle génère nativement les boxplots, heatmaps de corrélation et
distributions avec un code minimal. La heatmap `sns.heatmap(df.corr(), annot=True)`
est la forme canonique pour ce type d'analyse. Plotly Express reste disponible
pour les scatter plots interactifs si souhaité, mais Seaborn suffit pour un
notebook d'exploration reproductible.

**Alternatives considered**:
- Plotly Express seul : graphiques interactifs mais exports statiques moins
  pratiques pour la soutenance (PDF/HTML). Seaborn produit des figures
  Matplotlib directement intégrables dans le rapport.
- Pandas `.plot()` : insuffisant pour les boxplots groupés et les heatmaps annotées.

**Palette retenue**: `'Spectral'` pour les graphiques multicolores, `'coolwarm'`
pour la heatmap de corrélations (divergente, centre=0).

---

## 2. Encodage des variables catégorielles

**Decision**: Encodage manuel via mapping Python pour `sex` et `smoker`,
`pd.get_dummies(drop_first=True)` pour `region`.

**Rationale**: Le mapping manuel (`{'yes': 1, 'no': 0}`) est explicite, lisible
et cohérent avec le notebook `medical-cost-personal-dataset-eda-and-regression.ipynb`
déjà existant dans le repo. `pd.get_dummies` avec `drop_first=True` est la
méthode standard pour l'encodage one-hot dans pandas — elle évite la
multicolinéarité parfaite (dummy trap) et s'aligne avec la décision documentée
dans `research.md` de la feature 001 (northeast supprimé comme référence).

**Ordre des dummies pandas** (alphabétique) :
- northeast (supprimé — référence)
- northwest → `region_northwest`
- southeast → `region_southeast`
- southwest → `region_southwest`

**Alternatives considered**:
- `sklearn.OneHotEncoder` : plus verbeux, retourne un array numpy, perd les
  noms de colonnes sans configuration supplémentaire. Préféré en pipeline ML
  (feature 001) mais pas dans le notebook exploratoire.
- `sklearn.LabelEncoder` : non adapté aux variables nominales (impliquerait
  un ordre inexistant entre les régions).

---

## 3. Création de la target `categorie_risque`

**Decision**: `pd.cut()` avec les seuils définis dans la constitution.

**Rationale**: `pd.cut(charges, bins=[0, 5000, 15000, 30000, float('inf')],
labels=['faible', 'moyen', 'eleve', 'critique'])` est la méthode la plus lisible
et conforme aux seuils de la constitution. La borne inférieure à 0 garantit
que la valeur minimale de charges (≈ 1 122) est incluse.

**Seuils** (constitution Principe II) :
- faible : charges < 5 000 (borne inférieure : 0, exclusive left, inclusive right)
- moyen : 5 000 ≤ charges < 15 000
- élevé : 15 000 ≤ charges < 30 000
- critique : charges ≥ 30 000

**Distribution attendue** (estimation sur 1 338 lignes) :
- faible : ~25% (~335 lignes)
- moyen : ~50% (~669 lignes)
- élevé : ~18% (~240 lignes)
- critique : ~7% (~94 lignes)

Cette distribution est déséquilibrée — à documenter dans le notebook avec un
avertissement sur l'impact potentiel sur les métriques de classification.

---

## 4. Train/Test Split

**Decision**: `train_test_split(X, y, test_size=0.2, random_state=42,
stratify=y_classification)`.

**Rationale**: Le split 80/20 laisse ≈ 1 070 lignes en train et ≈ 268 en test
— suffisant pour RandomForest sur 1 338 lignes. `stratify=y_classification`
garantit que les proportions de chaque catégorie de risque sont préservées
dans les deux ensembles (essentiel vu le déséquilibre des classes). `random_state=42`
assure la reproductibilité (constitution Principe I).

**Note**: Pour la régression, le split est effectué sur les mêmes indices
(X_train/X_test partagés, y_train_reg/y_test_reg = charges correspondantes).

**Alternatives considered**:
- 70/30 : split minimum de la constitution — 80/20 est plus agressif et préférable
  avec seulement 1 338 lignes pour maximiser les données d'entraînement.
- Cross-validation k-fold : plus robuste mais complexifie le notebook pour peu
  de gain sur 1 338 lignes. Réservé à l'optimisation des hyperparamètres (hors scope).

---

## 5. Sauvegarde du dataset préparé

**Decision**: `features.csv` dans `data/processed/`, créé avec `df.to_csv(index=False)`.

**Rationale**: Le CSV est le format d'échange universel, lisible par pandas,
compatible avec les pipelines ML et versionnable (dans les limites du .gitignore
— features.csv n'est pas sensible donc peut être commité contrairement aux .pkl).

**Colonnes de `features.csv`** :
```
age, sexe, imc, enfants, fumeur, charges,
region_northwest, region_southeast, region_southwest,
categorie_risque
```

**Note** : `features.csv` contient le dataset complet (1 338 lignes) non splitté.
Le split est effectué en mémoire dans le notebook et dans les scripts d'entraînement
ML. Cela permet de recalculer facilement le split avec un autre random_state si besoin.

---

## 6. Structure des scripts `cleaning.py` et `normalization.py`

**Decision**: Fonctions pures sans état, sans lecture/écriture de fichiers.

**Rationale**: Les fonctions doivent être importables dans le pipeline ETL de
la feature 001 sans effet de bord. Le principe "un fichier = une responsabilité"
(constitution Principe V) justifie la séparation :
- `cleaning.py` = renommage uniquement (pas d'encodage)
- `normalization.py` = encodage uniquement (pas de renommage)

**Interface** :
```python
# cleaning.py
def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renomme les colonnes du dataset Kaggle vers le nommage métier français.
    
    Mapping : sex→sexe, bmi→imc, children→enfants, smoker→fumeur.
    Les colonnes non concernées (age, region, charges) sont conservées telles quelles.
    """

# normalization.py
def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Encode les variables catégorielles pour le ML.
    
    Encodages appliqués :
    - sexe : femme→1, homme→0 (si colonne 'sexe' présente)
    - fumeur : oui→1, non→0 (si colonne 'fumeur' présente)
    - region : one-hot avec drop_first=True (northeast supprimé)
    """
```

---

## 7. Graphiques du notebook 01

**Liste des 8 visualisations obligatoires** :

| # | Graphique | Type | Bibliothèque | Insight attendu |
|---|-----------|------|--------------|-----------------|
| 1 | Distribution de `charges` | Histogramme + KDE | Seaborn | Distribution bimodale, asymétrie droite |
| 2 | Boxplot `charges` par `smoker` | Boxplot groupé | Seaborn | Médiane fumeurs ≈ 3× non-fumeurs |
| 3 | Boxplot `charges` par `region` | Boxplot groupé | Seaborn | Distributions proches, SE légèrement plus élevé |
| 4 | Boxplot `charges` par `sex` | Boxplot groupé | Seaborn | Différence faible entre sexes |
| 5 | Scatter `age` vs `charges` | Scatter coloré | Seaborn/Plotly | 3 clusters visibles (fumeurs vs non-fumeurs) |
| 6 | Scatter `bmi` vs `charges` | Scatter coloré | Seaborn/Plotly | Seuil IMC ≈ 30 visible pour les fumeurs |
| 7 | Heatmap corrélations | Heatmap annotée | Seaborn | `smoker` corrélé à `charges` (≈ 0.79) |
| 8 | Distribution de chaque variable | Grille de subplots | Matplotlib/Seaborn | Vérification types et outliers |
