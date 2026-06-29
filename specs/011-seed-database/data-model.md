# Data Model: Seed Database

**Feature**: 011-seed-database | **Date**: 2026-06-13

## Entités impliquées

### Region (existante — lecture seule dans seed.py)

| Colonne | Type | Contrainte | Valeurs seed |
|---------|------|------------|--------------|
| `region_id` | SERIAL PK | auto | 1, 2, 3, 4 |
| `nom_region` | VARCHAR(50) | UNIQUE, IN (4 valeurs) | southwest, southeast, northwest, northeast |

**Action seed** : INSERT si `COUNT(*) = 0`, sinon skip.

---

### Client (existante — écrite par seed.py)

| Colonne BDD | Colonne CSV | Transformation |
|-------------|-------------|----------------|
| `region_id` | `region` | lookup dict `{nom_region: region_id}` |
| `age` | `age` | direct (int) |
| `sexe` | `sex` | `male`→`homme`, `female`→`femme` |
| `imc` | `bmi` | direct (float, arrondi à 2 décimales) |
| `enfants` | `children` | direct (int) |
| `fumeur` | `smoker` | `yes`→`True`, `no`→`False` |
| `email` | — | `NULL` |
| `telephone` | — | `NULL` |
| `date_creation` | — | `NOW()` (server default) |
| `date_suppression` | — | `NULL` (client actif) |

**Colonne CSV ignorée** : `charges` — donnée du dataset ML, pas insérée en base.

---

## Tables non touchées par seed.py

| Table | Raison |
|-------|--------|
| `predictions` | Remplie via `/api/predict/complet` au scoring |
| `contrats` | Créés par l'assureur via CRUD |
| `sinistres` | Déclarés par l'assureur via CRUD |
| `donnees_meteo` | Remplie via ETL OpenWeatherMap |
| `articles` | Remplie via ETL scraping |

---

## Flux de données seed.py

```
data/small_data/insurance.csv (1 338 lignes)
         │
         ▼
    pandas.read_csv()
         │
         ▼
    Transformations :
    sex → sexe, bmi → imc, children → enfants,
    smoker → fumeur, region → region_id (lookup)
         │
         ▼
    bulk_insert_mappings(Client, chunks de 500)
         │
         ▼
    PostgreSQL — table clients (1 338 lignes)
```
