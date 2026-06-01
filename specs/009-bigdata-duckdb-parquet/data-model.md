# Data Model: Big Data — DuckDB + Parquet 5M lignes

**Feature**: 009-bigdata-duckdb-parquet  
**Date**: 2026-06-01 (révisé après alignement BDD)  
**Type**: Vue dénormalisée Parquet — `clients` JOIN `predictions` simulés

## Fichier Parquet — insurance_big.parquet

**Chemin** : `data/big_data/insurance_big.parquet`  
**Lignes** : 5 000 000  
**Colonnes** : 14  
**Engine** : PyArrow  
**Compression** : Snappy (défaut PyArrow)  
**Index** : Aucun (`index=False`)

---

## Schéma des colonnes

### Bloc 1 — Variables clients (équivalent table `clients`)

| Colonne | Type Pandas | Valeurs / Plage | Génération |
| ------- | ----------- | --------------- | ---------- |
| `age` | `int32` | [18, 64] | `np.random.normal(μ_csv, σ_csv)` clippé + arrondi int |
| `sexe` | `category` | `homme`, `femme` | `np.random.choice` avec proportions CSV |
| `imc` | `float32` | [15.96, 53.13] | `np.random.normal(μ_csv, σ_csv)` clippé + round(2) |
| `enfants` | `int8` | {0, 1, 2, 3, 4, 5} | `np.random.choice` avec fréquences CSV |
| `fumeur` | `bool` | `True`, `False` | `np.random.choice` avec proportions CSV (~20.5% True) |
| `region` | `category` | 4 régions US | `np.random.choice` avec proportions CSV |

### Bloc 2 — Variables prédiction (équivalent table `predictions`)

| Colonne | Type Pandas | Valeurs / Plage | Génération |
| ------- | ----------- | --------------- | ---------- |
| `cout_predit` | `float32` | [1 121.0, 63 770.0] | Formule linéaire calibrée + bruit N(0, 4500), clippé |
| `categorie_risque` | `category` | `faible`, `moyen`, `eleve`, `critique` | `business.risk_engine.get_categorie_risque(cout_predit)` — seuils <5k/15k/30k |
| `decision` | `category` | `accepter`, `examiner`, `refuser` | `business.risk_engine.get_decision(categorie_risque)` |
| `prime` | `float32` | — | `business.scoring.calculer_prime(cout_predit, categorie_risque)` |
| `score_risque` | `float32` | [0.0, 1.0] | Probabilité simulée depuis `categorie_risque` + bruit gaussien clippé [0,1] |

**Simulation de `score_risque`** : intervalles par catégorie avec bruit N(0, 0.05) :

| `categorie_risque` | Intervalle cible | Probabilité typique |
| ------------------ | ---------------- | ------------------- |
| `faible` | [0.05, 0.25] | ~0.15 |
| `moyen` | [0.25, 0.50] | ~0.37 |
| `eleve` | [0.50, 0.75] | ~0.63 |
| `critique` | [0.75, 0.95] | ~0.85 |

### Bloc 3 — Features engineered (analytique pure)

| Colonne | Type Pandas | Valeurs | Calcul |
| ------- | ----------- | ------- | ------ |
| `cout_log` | `float32` | [~7.02, ~11.06] | `np.log1p(cout_predit)` |
| `tranche_age` | `category` | `jeune`, `adulte`, `senior`, `senior+` | age : 18-30 / 31-45 / 46-55 / 56-64 |
| `categorie_imc` | `category` | `sous-poids`, `normal`, `surpoids`, `obese` | seuils OMS : <18.5 / 18.5-25 / 25-30 / >30 |

---

## Formule de génération de `cout_predit`

```python
fumeur_flag = 1 si fumeur == True, sinon 0
sexe_femme_flag = 1 si sexe == 'femme', sinon 0

cout_brut = 256 * age
          + 339 * imc
          + 475 * enfants
          + 23800 * fumeur_flag
          - 130 * sexe_femme_flag
          - 12500
          + N(mean=0, std=4500)

cout_predit = clip(round(cout_brut, 2), 1121.0, 63770.0)
```

Coefficients calibrés sur le vrai dataset Kaggle (`data/small_data/insurance.csv`).

---

## Distributions issues du CSV source

| Variable | Distribution |
| -------- | ------------ |
| `age` | μ ≈ 39.2, σ ≈ 14.0, [18, 64] |
| `imc` | μ ≈ 30.7, σ ≈ 6.1, [15.96, 53.13] |
| `enfants` | 0→42.9%, 1→24.2%, 2→17.9%, 3→11.7%, 4→1.9%, 5→1.3% |
| `sexe` | homme ≈ 50.5%, femme ≈ 49.5% |
| `fumeur` | True ≈ 20.5%, False ≈ 79.5% |
| `region` | À extraire du CSV source (~25% par région) |

---

## Interface DuckDBAnalytics

**Chemin** : `big_data/duckdb_analytics.py`  
**Usage** : Importé directement par `streamlit_app/pages/2_📊_Analytics.py`

### Méthodes (9) — noms de colonnes alignés BDD

| Méthode | Colonnes retournées | Tri |
| ------- | ------------------- | --- |
| `stats_par_region()` | `region, nb, cout_moy, cout_med, cout_std, cout_min, cout_max` | `cout_moy` DESC |
| `stats_par_tranche_age()` | `tranche_age, nb, cout_moy, cout_med, cout_std, cout_min, cout_max` | ordre naturel tranche |
| `stats_par_fumeur()` | `fumeur, nb, cout_moy, score_risque_moy` | `fumeur` ASC |
| `distribution_cout()` | `bin_min, bin_max, nb` | `bin_min` ASC |
| `percentiles_cout()` | `p10, p25, p50, p75, p90, p95, p99` | — (1 ligne) |
| `correlation_age_cout()` | `age, cout_moy` | `age` ASC |
| `top_profils_risque()` | `tranche_age, categorie_imc, fumeur, score_risque_moy, nb` | `score_risque_moy` DESC LIMIT 10 |
| `evolution_imc_cout()` | `imc_bin, cout_moy` | `imc_bin` ASC |
| `stats_globales()` | `nb_total, cout_moy, score_risque_moy, age_moy, pct_fumeurs` | — (1 ligne) |

### Valeurs attendues

| Métrique | Valeur attendue |
| -------- | --------------- |
| `nb_total` | 5 000 000 |
| `cout_moy` global | ~13 000–15 000 USD |
| `pct_fumeurs` | ~20–21% |
| `age_moy` | ~39 ans |
| `cout_moy` fumeurs | ~2.5× non-fumeurs |
