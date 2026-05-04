# Tasks: ETL Pipeline 3 Sources

**Input**: Design documents from `/specs/006-etl-pipeline/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Organisation**: 3 user stories indépendantes — US1 (API météo), US2 (Scraping articles), US3 (SQL analytique).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1 : Setup (infrastructure commune)

**Objectif** : Créer les répertoires, modules Python et configuration partagés par les 3 user stories.

- [X] T001 Créer les dossiers `data_pipeline/extract/`, `data_pipeline/transform/`, `data_pipeline/load/` avec leurs `__init__.py`
- [X] T002 Créer `data/external/api_data/` et `data/external/scraped_data/` (répertoires de backup JSON)
- [X] T003 Ajouter `OPENWEATHER_API_KEY=` dans `.env` et `.env.example`
- [X] T004 Ajouter `data/external/` dans `.gitignore` (les backups JSON ne sont pas versionnés)

---

## Phase 2 : Fondation (couche de chargement partagée)

**Objectif** : Créer `db_loader.py` avec les fonctions d'insertion génériques réutilisées par US1 et US2.

- [X] T005 Créer `data_pipeline/load/db_loader.py` — fonctions : `insert_donnees_meteo(records: list[dict]) -> int` (utilise le modèle ORM `DonneesMeteo` de `database/models.py`, insertion simple) et `insert_articles(records: list[dict]) -> int` (utilise `Article`, `insert().on_conflict_do_nothing(index_elements=['url_source'])` via SQLAlchemy Core)

---

## Phase 3 : US1 — Collecte données météo via API OpenWeatherMap (P1)

**Objectif** : Pipeline complet météo — appel API → backup JSON → transformation → insertion `donnees_meteo`.

**Critère de test indépendant** : exécuter `python -m data_pipeline.extract.api_extractor`, vérifier 1 fichier JSON dans `data/external/api_data/` et 4 lignes dans `donnees_meteo`.

- [X] T006 [US1] Créer `data_pipeline/transform/transform_meteo.py` — fonctions : `determiner_saison(mois: int) -> str` (dict `{12:'hiver', 1:'hiver', ..., 3:'printemps', ...}`) et `transformer_reponse_api(reponse_json: dict, region_id: int) -> dict` (extrait `main.temp → temperature_moy`, `main.humidity → humidite_moy`, `rain.1h → precipitations` avec fallback 0.0, appelle `determiner_saison`)
- [X] T007 [US1] Créer `data_pipeline/extract/api_extractor.py` — constante `VILLES_REGIONS = {'southwest': 'Phoenix,US', 'southeast': 'Atlanta,US', 'northwest': 'Seattle,US', 'northeast': 'Boston,US'}`, fonctions : `_build_region_lookup(db) -> dict[str, int]` (SELECT dans `regions`), `appeler_api(ville: str, api_key: str) -> dict` (GET `https://api.openweathermap.org/data/2.5/weather?q={ville}&appid={key}&units=metric`, timeout=10, lève ValueError si status != 200), `sauvegarder_backup(data: list, dossier: str) -> str` (écrit `meteo_{YYYYMMDD_HHMMSS}.json`), `main()` (orchestre : lecture clé depuis `.env`, lookup regions, 4 appels API, backup, transformation via `transform_meteo`, insertion via `db_loader.insert_donnees_meteo`)
- [ ] T008 [US1] EN ATTENTE activation clé API (jusqu'à 2h) — Vérifier l'exécution standalone : `python -m data_pipeline.extract.api_extractor` (nécessite une vraie clé API dans `.env`)

---

## Phase 4 : US2 — Scraping articles santemagazine.fr (P2)

**Objectif** : Pipeline complet scraping — requête HTTP → parse HTML → backup JSON → transformation → insertion `articles`.

**Critère de test indépendant** : exécuter `python -m data_pipeline.extract.scraper`, vérifier 1 fichier JSON dans `data/external/scraped_data/` et au moins 5 lignes dans `articles`.

- [X] T009 [US2] Créer `data_pipeline/transform/transform_articles.py` — fonctions : `nettoyer_html(texte: str) -> str` (BeautifulSoup pour supprimer les balises, strip, normalisation espaces), `normaliser_date(date_str: str) -> datetime | None` (essaie plusieurs formats : `%Y-%m-%d`, `%d %B %Y` en français, `dateutil.parser.parse` en fallback, retourne None si échec), `transformer_articles(articles_bruts: list[dict]) -> list[dict]` (applique nettoyage HTML sur titre et résumé, normalise dates, déduplique par URL, retourne liste de dicts prêts pour insertion)
- [X] T010 [US2] Créer `data_pipeline/extract/scraper.py` — constante `URL_CIBLE = 'https://www.santemagazine.fr/actualites'`, fonctions : `scraper_articles(url: str, timeout: int = 10) -> list[dict]` (requests.get avec headers User-Agent, try/except `requests.exceptions.RequestException` → log erreur + return [], BeautifulSoup parse les balises `article` ou `h2+a`, extrait titre/href/résumé/date), `construire_url_absolue(href: str, base_url: str) -> str`, `sauvegarder_backup(articles: list, dossier: str) -> str` (écrit `articles_{YYYYMMDD_HHMMSS}.json`), `main()` (orchestre : scraping, backup, transformation via `transform_articles`, insertion via `db_loader.insert_articles`)
- [X] T011 [US2] Vérifier l'exécution standalone : `python -m data_pipeline.extract.scraper` et contrôler le nombre d'articles insérés

---

## Phase 5 : US3 — Requêtes SQL analytiques complexes (P3)

**Objectif** : Créer `database/queries.sql` avec 10+ requêtes documentées démontrant C4 (jointures) et C5 (agrégations).

**Critère de test indépendant** : exécuter `psql -U assuml_user -d assuml_db -f database/queries.sql` sans erreur.

- [X] T012 [US3] Créer `database/queries.sql` avec les 10 requêtes suivantes (chacune précédée d'un commentaire -- décrivant son objectif) :
  1. Liste clients avec leur nom de région (JOIN clients × regions)
  2. Nombre de clients par région (GROUP BY regions.nom_region)
  3. IMC moyen et âge moyen par région (AVG + GROUP BY)
  4. Régions avec plus de 100 clients fumeurs (GROUP BY + HAVING)
  5. Coût médical prédit moyen par catégorie de risque (JOIN clients × predictions + GROUP BY)
  6. Clients sans aucune prédiction (LEFT JOIN predictions IS NULL)
  7. Top 5 clients par coût prédit avec leur région (sous-requête ou RANK() OVER)
  8. Répartition fumeurs/non-fumeurs par région en % (GROUP BY multi-colonnes + calcul pourcentage)
  9. Clients avec contrats actifs et prime mensuelle — 3 tables (clients JOIN regions JOIN contrats WHERE statut='actif')
  10. Tableau de bord par région : nb clients, IMC moyen, % fumeurs, coût prédit moyen (multi-agrégations sur 2 tables)
- [X] T013 [US3] Exécuter `psql -U assuml_user -d assuml_db -f database/queries.sql` et vérifier que toutes les requêtes s'exécutent sans erreur

---

## Phase 6 : Polish et conformité

**Objectif** : Qualité du code, idempotence, vérification gitignore.

- [ ] T014 [P] EN ATTENTE clé API — Vérifier l'idempotence du pipeline météo : exécuter `api_extractor.py` deux fois et contrôler que `donnees_meteo` a exactement 8 lignes (2 × 4 régions) — historisation correcte
- [X] T015 [P] Vérifier l'idempotence du scraper : exécuter `scraper.py` deux fois et contrôler que le COUNT dans `articles` est identique à la seconde exécution (ON CONFLICT DO NOTHING)
- [X] T016 Vérifier PEP8 + black sur `data_pipeline/` et `database/queries.sql` : `flake8 data_pipeline/ --max-line-length=88`
- [X] T017 Vérifier que `data/external/` est bien ignoré par git : `git status` ne doit pas montrer les fichiers JSON de backup

---

## Dépendances

```
T001 → T002 → T003 → T004 (séquentiels — setup)
T005 (fondation, requis par T007 et T010)
T006 → T007 → T008 (US1, séquentiels)
T009 → T010 → T011 (US2, séquentiels)
T005 doit précéder T007 et T010
T012 → T013 (US3, séquentiels, indépendant de US1 et US2)
T014, T015 requièrent T008 et T011 respectivement
T016, T017 après toutes les implémentations
```

**User stories indépendantes** : US1, US2 et US3 peuvent être implémentées en parallèle après T005 (fondation).

## Exemples d'exécution parallèle

```bash
# Après T005 :
python -m data_pipeline.extract.api_extractor &   # US1
python -m data_pipeline.extract.scraper &          # US2
# US3 : éditer database/queries.sql indépendamment
```

## Stratégie d'implémentation

**MVP (US1 seule)** : T001-T005 + T006-T008 — pipeline météo fonctionnel avec backup et insertion. Suffit à démontrer la compétence C1 avec la source API.

**Livraison complète** : US1 + US2 + US3 — 3 sources démontrées, 10 requêtes SQL analytiques.

**Ordre recommandé** :
1. Setup (T001-T004) — 10 min
2. db_loader (T005) — 30 min
3. US1 météo (T006-T008) — 45 min
4. US2 scraping (T009-T011) — 60 min
5. US3 SQL (T012-T013) — 45 min
6. Polish (T014-T017) — 20 min
