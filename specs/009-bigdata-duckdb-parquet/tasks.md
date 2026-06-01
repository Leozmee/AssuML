# Tasks: Big Data — DuckDB + Parquet 5M lignes

**Input**: Design documents from `/specs/009-bigdata-duckdb-parquet/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅
**Dépendance**: 008-streamlit-app ✅ (placeholder Analytics disponible dans `2_📊_Analytics.py`)

**Organisation**: 3 stories séquentielles — génération → analytics → visualisation.
Tests requis par la constitution (Principe V).

---

## Phase 1: Setup (Infrastructure)

**Purpose**: Initialiser le module `big_data/`, configurer le gitignore, vérifier les dépendances.

- [X] T001 Créer `big_data/__init__.py` (module Python vide)
- [X] T002 Ajouter `data/big_data/` au `.gitignore` (le Parquet ne doit pas être commité)
- [X] T003 Installer DuckDB et PyArrow : `pip install duckdb pyarrow` et mettre à jour `requirements.txt`

**Checkpoint**: `import duckdb; import pyarrow` sans erreur dans le shell Python. ✅

---

## Phase 2: Foundational (Prérequis bloquants)

**Purpose**: Aucun prérequis bloquant inter-stories — chaque story peut démarrer dès le Setup. Cependant, l'ordre d'exécution pratique est US1 → US2 → US3 car US2 et US3 nécessitent le fichier Parquet produit par US1.

**⚠️ NOTE** : Les tests US2 utilisent une fixture Parquet minimale (1 000 lignes) et sont indépendants du script US1.

---

## Phase 3: User Story 1 — Génération Parquet (Priority: P1) 🎯 MVP

**Goal**: Produire `data/big_data/insurance_big.parquet` (5M lignes, 14 colonnes) en moins de 2 minutes.

**Independent Test**: `python big_data/generate_synthetic.py` → fichier créé ; `import pandas as pd; df = pd.read_parquet('data/big_data/insurance_big.parquet'); assert len(df) == 5_000_000` passe.

- [X] T004 [US1] Créer `big_data/generate_synthetic.py` avec imports (numpy, pandas, pathlib, time, business.risk_engine, business.scoring), np.random.seed(42), lecture de `data/small_data/insurance.csv` et extraction des distributions (μ/σ de age et imc, fréquences relatives de enfants, proportions de sexe/fumeur/region)
- [X] T005 [US1] Implémenter la génération des colonnes clients dans `big_data/generate_synthetic.py` : age (normal clippé [18,64] → int), imc (normal clippé [15.96,53.13] → round 2), enfants (np.random.choice avec probs CSV), sexe (`homme`/`femme`), fumeur (bool), region (np.random.choice avec proportions CSV)
- [X] T006 [US1] Implémenter la formule de `cout_predit` dans `big_data/generate_synthetic.py` : `256*age + 339*imc + 475*enfants + 23800*fumeur_flag - 130*sexe_femme_flag - 12500 + N(0,4500)`, clipping [1121, 63770], round(2)
- [X] T007 [US1] Implémenter les colonnes prédiction dans `big_data/generate_synthetic.py` : `categorie_risque` et `decision` via `business.risk_engine`, `prime` via `business.scoring.calculer_prime()`, `score_risque` simulé par intervalle par catégorie + bruit N(0,0.05) clippé [0,1]
- [X] T008 [US1] Implémenter les features engineered dans `big_data/generate_synthetic.py` : `cout_log` (np.log1p), `tranche_age` (18-30/31-45/46-55/56-64), `categorie_imc` (seuils OMS), puis sauvegarder avec PyArrow (pas d'index) + afficher temps et taille du fichier
- [X] T009 [P] [US1] Créer `tests/unit/test_generate_synthetic.py` : vérifier les 14 colonnes et leurs types, que `cout_predit` ∈ [1121, 63770], que `age` ∈ [18, 64], que `fumeur` est bien booléen, que `score_risque` ∈ [0, 1]

**Checkpoint**: `python big_data/generate_synthetic.py` → `data/big_data/insurance_big.parquet` créé en < 2 minutes, 5 000 000 lignes, 14 colonnes. ✅

---

## Phase 4: User Story 2 — Module DuckDBAnalytics (Priority: P2)

**Goal**: Classe `DuckDBAnalytics` avec 9 méthodes retournant des DataFrames Pandas, chacune < 5 secondes sur 5M lignes.

**Independent Test**: `from big_data.duckdb_analytics import DuckDBAnalytics; a = DuckDBAnalytics('data/big_data/insurance_big.parquet'); df = a.stats_globales(); assert df['nb_total'].iloc[0] == 5_000_000`

- [X] T010 [US2] Créer `big_data/duckdb_analytics.py` avec classe `DuckDBAnalytics`, `__init__(self, parquet_path: str)` stockant le chemin et ouvrant une connexion DuckDB in-memory (`duckdb.connect()`)
- [X] T011 [US2] Implémenter `stats_par_region()` et `stats_par_tranche_age()` dans `big_data/duckdb_analytics.py` : agrégats COUNT/AVG/MEDIAN/STDDEV/MIN/MAX sur `cout_predit` par `region` et par `tranche_age` via `read_parquet()`
- [X] T012 [US2] Implémenter `stats_par_fumeur()` et `distribution_cout()` dans `big_data/duckdb_analytics.py` : comparaison fumeurs/non-fumeurs sur `cout_predit` et `score_risque` + histogramme bins 5000$ avec `floor(cout_predit/5000)*5000 AS bin_min`
- [X] T013 [US2] Implémenter `percentiles_cout()` et `correlation_age_cout()` dans `big_data/duckdb_analytics.py` : percentiles via `PERCENTILE_CONT` sur `cout_predit` et moyenne `cout_predit` par `age` (18→64)
- [X] T014 [US2] Implémenter `top_profils_risque()` et `evolution_imc_cout()` dans `big_data/duckdb_analytics.py` : top 10 combinaisons (`tranche_age`, `categorie_imc`, `fumeur`) par `score_risque` moyen + moyenne `cout_predit` par tranche `imc` (bins 2 pts)
- [X] T015 [US2] Implémenter `stats_globales()` dans `big_data/duckdb_analytics.py` : COUNT total, AVG `cout_predit`, AVG `score_risque`, AVG `age`, proportion `fumeur` True (retourne 1 ligne)
- [X] T016 [P] [US2] Créer `tests/unit/test_duckdb_analytics.py` : fixture pytest générant un Parquet minimal 1 000 lignes (14 colonnes, même schéma), tester les 9 méthodes (DataFrame non vide, colonnes correctes, valeurs cohérentes)

**Checkpoint**: `pytest tests/unit/test_duckdb_analytics.py -v` → tous les tests passent. ✅

---

## Phase 5: User Story 3 — Tableau de bord Streamlit (Priority: P3)

**Goal**: Page `2_📊_Analytics.py` complète avec 6 sections Plotly alimentées par DuckDB, remplaçant le placeholder Feature 7.

**Independent Test**: `streamlit run streamlit_app/app.py` → page Analytics affiche métriques + 6 sections sans erreur ; si Parquet absent → message d'erreur clair.

- [X] T017 [US3] Réécrire l'en-tête de `streamlit_app/pages/2_📊_Analytics.py` : imports (streamlit, plotly.express, sys/pathlib pour ajouter la racine au path), `st.cache_resource` pour instancier `DuckDBAnalytics`, gestion `FileNotFoundError` avec `st.error()` + `st.stop()`
- [X] T018 [US3] Implémenter les métriques globales en haut de page dans `streamlit_app/pages/2_📊_Analytics.py` : appel `stats_globales()` en cache (`st.cache_data(ttl=300)`), affichage 5 `st.metric()` en colonnes (nb lignes, coût moyen, score risque moyen, âge moyen, % fumeurs)
- [X] T019 [US3] Implémenter Section 1 "Analyse par région" dans `streamlit_app/pages/2_📊_Analytics.py` : `stats_par_region()` → `px.bar()` coût moyen par région + `st.dataframe()` tableau détaillé, dans `st.expander()`
- [X] T020 [US3] Implémenter Section 2 "Impact du tabac" dans `streamlit_app/pages/2_📊_Analytics.py` : `stats_par_fumeur()` → `px.bar()` grouped (coût moy + score risque moy, fumeurs vs non-fumeurs), dans `st.expander()`
- [X] T021 [US3] Implémenter Section 3 "Distribution des coûts" dans `streamlit_app/pages/2_📊_Analytics.py` : `distribution_cout()` → `px.bar()` histogramme bins 5 000 USD, axe X labels en K$, dans `st.expander()`
- [X] T022 [US3] Implémenter Section 4 "Corrélation âge-coût" dans `streamlit_app/pages/2_📊_Analytics.py` : `correlation_age_cout()` → `px.line()` coût moyen prédit par âge, dans `st.expander()`
- [X] T023 [US3] Implémenter Section 5 "Profils à risque" et Section 6 "Percentiles" dans `streamlit_app/pages/2_📊_Analytics.py` : `top_profils_risque()` → `st.dataframe()` top 10 ; `percentiles_cout()` → 7 `st.metric()` alignés (P10 à P99)
- [X] T024 [US3] Ajouter le footer `st.caption("5 000 000 lignes analysées via DuckDB")` et vérifier cohérence visuelle (thème Plotly uniforme `template="plotly_white"`) dans `streamlit_app/pages/2_📊_Analytics.py`

**Checkpoint**: Page Analytics s'affiche avec 5 métriques + 6 sections ; `st.error()` apparaît si le Parquet est renommé. ✅

---

## Phase 6: Polish & Tests finaux

- [X] T025 [P] Vérifier conformité PEP 8 : `flake8 big_data/ --max-line-length=88` et `black --check big_data/ streamlit_app/pages/2_📊_Analytics.py`
- [X] T026 Lancer `pytest tests/unit/test_generate_synthetic.py tests/unit/test_duckdb_analytics.py -v` et corriger les éventuels échecs
- [X] T027 Mettre à jour la commande Big Data dans `CLAUDE.md` : remplacer `python data_pipeline/generate_synthetic.py` par `python big_data/generate_synthetic.py`

---

## Dépendances & Ordre d'exécution

### Dépendances entre phases

- **Setup (Phase 1)** : aucune dépendance — démarrage immédiat
- **US1 (Phase 3)** : dépend de Phase 1 (Setup)
- **US2 (Phase 4)** : dépend de Phase 1 pour le code ; le Parquet 5M lignes produit par US1 est nécessaire pour la validation manuelle ; les tests utilisent une fixture indépendante
- **US3 (Phase 5)** : dépend de US2 (importe `DuckDBAnalytics`) et nécessite le Parquet pour la validation Streamlit
- **Polish (Phase 6)** : dépend de US1 + US2 + US3

### Dépendances dans chaque story

```
T001 → T002 → T003 (séquentiels Setup)

US1 : T004 → T005 → T006 → T007 → T008 (séquentiels, même fichier)
      T009 [P] peut être écrit en parallèle de T004-T008

US2 : T010 → T011 → T012 → T013 → T014 → T015 (séquentiels, même fichier)
      T016 [P] peut être écrit en parallèle de T010-T015

US3 : T017 → T018 → T019 → T020 → T021 → T022 → T023 → T024 (séquentiels, même fichier)
```

### Parallélisme

Seuls T009 (tests US1) et T016 (tests US2) sont marqués [P] car ils s'écrivent dans des fichiers de test distincts, sans dépendre du code de production pour leur squelette.

---

## Parallel Example: User Story 2

```bash
# Écrire le squelette de tests en parallèle du code :
Task T016: "tests/unit/test_duckdb_analytics.py — fixture + assertions"
Task T010-T015: "big_data/duckdb_analytics.py — 9 méthodes DuckDB"
```

---

## Implementation Strategy

### MVP (User Story 1 only)

1. Compléter Phase 1 : Setup
2. Compléter Phase 3 : US1 (T004–T009)
3. **Valider** : `python big_data/generate_synthetic.py` → Parquet 5M lignes
4. `pytest tests/unit/test_generate_synthetic.py` → ✅

### Livraison incrémentale

1. Setup + US1 → Parquet disponible (MVP)
2. + US2 → 9 méthodes analytiques testées (démo data science)
3. + US3 → Dashboard Streamlit complet (démo utilisateur)
4. + Polish → conformité flake8/black, tests green

---

## Notes

- `[P]` = fichier distinct, peut s'écrire en parallèle du code de production
- `[US1/2/3]` = traçabilité story → tâche
- Les tests utilisent une fixture Parquet 1 000 lignes (rapide, indépendante des 5M lignes)
- La connexion DuckDB est `st.cache_resource` (session unique Streamlit) — les DataFrames résultats sont `st.cache_data(ttl=300)`
- Ne pas commiter `data/big_data/insurance_big.parquet` (`.gitignore`)
