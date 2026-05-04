# Quickstart: ETL Pipeline 3 Sources

**Branch**: `006-etl-pipeline` | **Date**: 2026-05-04

## Prérequis

1. PostgreSQL actif avec `assuml_db` peuplée (Feature 005 déployée)
2. `.env` à la racine du projet avec :
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=assuml_db
   DB_USER=assuml_user
   DB_PASS=assuml_pass
   OPENWEATHER_API_KEY=<ta_clé_API>
   ```
3. Venv activé avec les dépendances installées

## Scénario 1 — Collecte météo (US1)

```bash
# Exécuter l'extracteur API
python -m data_pipeline.extract.api_extractor

# Vérifier le backup JSON
ls data/external/api_data/

# Vérifier l'insertion en base
psql -U assuml_user -d assuml_db -c "SELECT * FROM donnees_meteo ORDER BY date_collecte DESC LIMIT 4;"
```

**Résultat attendu** :
- 1 fichier `meteo_YYYYMMDD_HHMMSS.json` dans `data/external/api_data/`
- 4 nouvelles lignes dans `donnees_meteo` (une par région)
- Saison correcte pour le mois en cours
- `precipitations = 0.0` si pas de pluie

## Scénario 2 — Scraping articles (US2)

```bash
# Exécuter le scraper
python -m data_pipeline.extract.scraper

# Vérifier le backup JSON
ls data/external/scraped_data/

# Vérifier l'insertion en base
psql -U assuml_user -d assuml_db -c "SELECT titre, nom_source, date_publication FROM articles LIMIT 5;"
```

**Résultat attendu** :
- 1 fichier `articles_YYYYMMDD_HHMMSS.json` dans `data/external/scraped_data/`
- Au moins 5 articles dans la table `articles`
- Pas d'erreur si `url_source` déjà présente (ON CONFLICT DO NOTHING)

## Scénario 3 — Test d'idempotence

```bash
# Exécuter deux fois de suite
python -m data_pipeline.extract.api_extractor
python -m data_pipeline.extract.api_extractor

# Vérifier qu'il y a 8 lignes dans donnees_meteo (2 exécutions × 4 régions)
psql -U assuml_user -d assuml_db -c "SELECT COUNT(*) FROM donnees_meteo;"

# Exécuter le scraper deux fois
python -m data_pipeline.extract.scraper
python -m data_pipeline.extract.scraper

# Vérifier que le nombre d'articles n'a pas doublé
psql -U assuml_user -d assuml_db -c "SELECT COUNT(*) FROM articles;"
```

**Résultat attendu** :
- `donnees_meteo` : +4 lignes par exécution (historisation)
- `articles` : count identique à la seconde exécution (ON CONFLICT DO NOTHING)

## Scénario 4 — Requêtes SQL analytiques (US3)

```bash
# Exécuter toutes les requêtes du fichier
psql -U assuml_user -d assuml_db -f database/queries.sql

# Ou exécuter une requête individuelle
psql -U assuml_user -d assuml_db -c "
  SELECT r.nom_region, COUNT(c.client_id) AS nb_clients
  FROM regions r
  JOIN clients c ON c.region_id = r.region_id
  GROUP BY r.nom_region
  ORDER BY nb_clients DESC;
"
```

**Résultat attendu** :
- Aucune erreur SQL
- Résultats cohérents avec les 1 338 clients chargés

## Scénario 5 — Clé API invalide (test d'erreur)

```bash
# Temporairement mettre une clé invalide dans .env
OPENWEATHER_API_KEY=cle_invalide python -m data_pipeline.extract.api_extractor
```

**Résultat attendu** :
- Message d'erreur explicite (401 ou similaire)
- Pas de fichier JSON partiel créé
- La base de données n'est pas modifiée

## Structure des fichiers produits

```
data/external/
├── api_data/
│   ├── meteo_20260504_143022.json   # Réponses brutes OpenWeatherMap
│   └── meteo_20260504_151145.json   # Exécution suivante
└── scraped_data/
    ├── articles_20260504_143500.json  # Articles bruts scrappés
    └── articles_20260504_160000.json  # Exécution suivante
```
