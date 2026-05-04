# Data Model: ETL Pipeline 3 Sources

**Branch**: `006-etl-pipeline` | **Date**: 2026-05-04

## Entités existantes réutilisées (Feature 005)

Les entités ci-dessous sont déjà définies dans `database/models.py` et `database/schema.sql`. Cette feature les **peuple** — elle ne les modifie pas.

---

### DonneesMeteo

**Table** : `donnees_meteo`

| Champ | Type | Contrainte | Source |
|---|---|---|---|
| `meteo_id` | SERIAL | PK, auto | auto |
| `region_id` | INTEGER | FK → regions, NOT NULL | lookup depuis `regions` par nom de ville |
| `temperature_moy` | DECIMAL(5,2) | CHECK [-50, 60] | `main.temp` (API) |
| `humidite_moy` | DECIMAL(5,2) | CHECK [0, 100] | `main.humidity` (API) |
| `precipitations` | DECIMAL(5,2) | CHECK >= 0 | `rain.1h` ou 0 si absent (API) |
| `saison` | VARCHAR(20) | CHECK printemps/ete/automne/hiver | calculé depuis mois courant |
| `date_collecte` | TIMESTAMP | NOT NULL, DEFAULT NOW() | horodatage insertion |

**Relations** :
- `region_id` → `regions.region_id` (ON DELETE CASCADE)

**Règles métier** :
- Une exécution = 4 lignes (une par région)
- Historisation : pas de TRUNCATE, les anciennes lignes sont conservées
- `precipitations` vaut 0.0 si l'API ne retourne pas de champ `rain` (temps sec)

---

### Article

**Table** : `articles`

| Champ | Type | Contrainte | Source |
|---|---|---|---|
| `article_id` | SERIAL | PK, auto | auto |
| `titre` | VARCHAR(500) | NOT NULL | balise `<h2>` ou `<title>` (scraping) |
| `url_source` | TEXT | UNIQUE, NOT NULL | href absolu de l'article (scraping) |
| `nom_source` | VARCHAR(100) | NOT NULL | nom du site (constante = `"santemagazine.fr"`) |
| `resume` | TEXT | NULL | premier `<p>` de l'article ou méta description |
| `date_publication` | TIMESTAMP | NULL | balise `<time>` ou méta `article:published_time` |
| `date_scraping` | TIMESTAMP | NOT NULL, DEFAULT NOW() | horodatage insertion |

**Relations** :
- Aucune FK (table autonome)

**Règles métier** :
- Déduplication par `url_source` : `ON CONFLICT (url_source) DO NOTHING`
- `resume` tronqué à 2 000 caractères si nécessaire (TEXT est illimité en PG, mais la valeur scrappée peut être longue)
- `date_publication` reste NULL si non trouvée plutôt que de générer une date incorrecte

---

## Entités en mémoire (non persistées)

### RéponseAPI (structure intermédiaire)

Représente une réponse JSON brute de l'API OpenWeatherMap avant transformation.

| Champ JSON | Champ extrait | Transformation |
|---|---|---|
| `main.temp` | `temperature_moy` | float, arrondi à 2 décimales |
| `main.humidity` | `humidite_moy` | int → float |
| `rain.1h` | `precipitations` | float ou 0.0 si absent |
| `name` | *(ignoré)* | nom de ville de l'API |
| `dt` | *(ignoré)* | timestamp Unix, non stocké (on utilise `date_collecte`) |

### ArticleBrut (structure intermédiaire)

Représente un article scrappé avant nettoyage et insertion.

| Attribut | Description |
|---|---|
| `titre` | Texte brut, peut contenir des entités HTML |
| `url` | URL relative ou absolue selon le site |
| `resume` | HTML brut, peut contenir des balises `<span>`, `<strong>` |
| `date_str` | Chaîne de date non normalisée (ex. "15 avril 2026") |

---

## Flux de données

```
[OpenWeatherMap API]
        ↓
api_extractor.py → JSON brut → data/external/api_data/meteo_{ts}.json
        ↓
transform_meteo.py → liste de dict {region_id, temp, humidite, pluie, saison}
        ↓
db_loader.insert_donnees_meteo() → table donnees_meteo

[santemagazine.fr]
        ↓
scraper.py → HTML brut → data/external/scraped_data/articles_{ts}.json
        ↓
transform_articles.py → liste de dict {titre, url, source, resume, date_pub}
        ↓
db_loader.insert_articles() → table articles (ON CONFLICT DO NOTHING)
```

---

## Lookup ville → region_id

| Ville | region_id | nom_region |
|---|---|---|
| Phoenix, AZ | 1 | southwest |
| Atlanta, GA | 2 | southeast |
| Seattle, WA | 3 | northwest |
| Boston, MA | 4 | northeast |

Le `region_id` réel est résolu dynamiquement via `SELECT region_id FROM regions WHERE nom_region = ?` — pas de valeur hardcodée.
