# Feature Specification: ETL Pipeline 3 Sources

**Feature Branch**: `006-etl-pipeline`
**Created**: 2026-05-04
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Collecte données météo via API (Priority: P1)

En tant que data engineer, je veux que le pipeline récupère automatiquement les données météo des 4 régions US depuis une source externe, les transforme et les stocke en base, afin d'enrichir le dataset d'assurance avec des variables contextuelles.

**Why this priority**: Les données météo constituent la source externe la plus structurée et la plus fiable. Elle démontre la compétence C1 (collecte via API) de façon autonome et est indépendante du scraping.

**Independent Test**: Peut être testée seule en exécutant `api_extractor.py`, en vérifiant qu'un fichier JSON de sauvegarde est créé dans `data/external/api_data/` et qu'au moins une ligne apparaît dans la table `donnees_meteo`.

**Acceptance Scenarios**:

1. **Given** une clé API valide dans `.env`, **When** `api_extractor.py` est exécuté, **Then** les données des 4 régions sont récupérées et stockées dans `donnees_meteo` avec les bons `region_id`.
2. **Given** les données brutes de l'API, **When** `transform_meteo.py` est appelé, **Then** la saison est correctement déterminée depuis la date (printemps/été/automne/hiver) et les champs non pertinents sont éliminés.
3. **Given** une clé API invalide ou absente, **When** `api_extractor.py` est exécuté, **Then** une erreur explicite est levée sans corrompre les données existantes.
4. **Given** des données météo déjà présentes en base, **When** `api_extractor.py` est exécuté une seconde fois, **Then** de nouvelles lignes sont insérées (historisation par date de collecte, pas de suppression des précédentes).

---

### User Story 2 - Scraping articles assurance/santé (Priority: P2)

En tant que data engineer, je veux que le pipeline scrape automatiquement des articles d'actualité assurance ou santé depuis un site francophone public, les nettoie et les insère en base, afin de disposer d'une troisième source hétérogène démontrant la compétence C1.

**Why this priority**: Le scraping démontre une compétence distincte de l'API. La priorité P2 est justifiée car le scraping est plus fragile (dépendance à la structure HTML du site cible) et peut être livré indépendamment.

**Independent Test**: Peut être testée seule en exécutant `scraper.py`, en vérifiant que `data/external/scraped_data/articles_raw.json` contient des données et qu'au moins un article est inséré dans la table `articles`.

**Acceptance Scenarios**:

1. **Given** un accès réseau fonctionnel, **When** `scraper.py` est exécuté, **Then** au moins 5 articles sont extraits avec titre, URL, nom de source, résumé et date.
2. **Given** des articles récupérés, **When** `transform_articles.py` traite les données, **Then** le HTML brut est nettoyé, les dates sont normalisées et les doublons par URL sont supprimés avant insertion.
3. **Given** un article dont l'URL existe déjà en base, **When** l'insertion est tentée, **Then** l'article est silencieusement ignoré (pas d'erreur, pas de mise à jour).
4. **Given** les données brutes du scraping, **When** le backup est effectué, **Then** un fichier JSON est créé dans `data/external/scraped_data/` avant toute insertion.

---

### User Story 3 - Requêtes SQL analytiques complexes (Priority: P3)

En tant qu'analyste ou évaluateur du projet, je veux disposer d'un fichier `database/queries.sql` contenant des requêtes SQL documentées et complexes, afin de démontrer les compétences C4 (jointures) et C5 (agrégations, sous-requêtes).

**Why this priority**: Cette user story est indépendante du pipeline ETL. Elle peut être livrée séparément car elle ne génère pas de données — elle documente la capacité d'analyse SQL sur les données existantes.

**Independent Test**: Peut être testée seule en exécutant chaque requête dans `psql` et en vérifiant que toutes retournent un résultat sans erreur sur la base peuplée avec les 1 338 clients.

**Acceptance Scenarios**:

1. **Given** la base `assuml_db` avec des données dans `clients`, `regions`, `predictions`, `contrats`, `sinistres`, **When** les requêtes du fichier sont exécutées, **Then** chacune retourne un résultat sans erreur.
2. **Given** le fichier `queries.sql`, **When** un évaluateur le consulte, **Then** il contient au moins 10 requêtes documentées couvrant jointures multi-tables, GROUP BY + HAVING, sous-requêtes et agrégations statistiques.
3. **Given** la table `clients` avec 1 338 lignes, **When** les requêtes d'agrégation sont exécutées, **Then** les totaux par région, sexe et statut fumeur correspondent aux données insérées par `load_csv.py`.

---

### Edge Cases

- Que se passe-t-il si l'API OpenWeatherMap retourne une erreur 429 (rate limit) ?
- Que se passe-t-il si le site cible du scraping est indisponible ou a changé sa structure HTML ?
- Que se passe-t-il si `data/external/api_data/` ou `data/external/scraped_data/` n'existent pas ?
- Que se passe-t-il si une donnée météo viole une contrainte CHECK (ex. température hors [-50, 60]) ?
- Que se passe-t-il si le titre ou l'URL d'un article est vide ou trop long ?

## Requirements *(mandatory)*

### Functional Requirements

**Source 2 — API météo :**

- **FR-001**: Le pipeline DOIT appeler l'API météo pour les 4 villes (Phoenix → southwest, Atlanta → southeast, Seattle → northwest, Boston → northeast) et mapper chaque ville à son `region_id` via lookup en base.
- **FR-002**: Les réponses JSON brutes DOIVENT être sauvegardées dans `data/external/api_data/` avant toute transformation ou insertion.
- **FR-003**: Le pipeline DOIT extraire depuis la réponse API : température moyenne, humidité moyenne et précipitations.
- **FR-004**: La clé API DOIT être lue exclusivement depuis la variable d'environnement `OPENWEATHER_API_KEY` — aucun credential dans le code.
- **FR-005**: La saison DOIT être déterminée automatiquement depuis la date de collecte : printemps (mars-mai), été (juin-août), automne (septembre-novembre), hiver (décembre-février).
- **FR-006**: Les données transformées DOIVENT être insérées dans `donnees_meteo` avec le `region_id` correct et la date de collecte.

**Source 3 — Scraping :**

- **FR-007**: Le scraper DOIT extraire depuis un site francophone public accessible sans authentification : titre, URL, nom de source, résumé et date de publication pour chaque article.
- **FR-008**: Les données brutes DOIVENT être sauvegardées dans `data/external/scraped_data/articles_raw.json` avant transformation.
- **FR-009**: La transformation DOIT nettoyer les balises HTML résiduelles, normaliser les dates et dédupliquer les articles par URL avant insertion.
- **FR-010**: L'insertion DOIT gérer les doublons via la contrainte UNIQUE sur `url_source` (ON CONFLICT DO NOTHING) — jamais d'erreur pour un article déjà présent.

**Couche de chargement :**

- **FR-011**: `data_pipeline/load/db_loader.py` DOIT fournir des fonctions génériques `insert_donnees_meteo(records)` et `insert_articles(records)` utilisables indépendamment par les deux sources.

**Requêtes SQL :**

- **FR-012**: `database/queries.sql` DOIT contenir au minimum 10 requêtes documentées (commentaires SQL) couvrant : jointures clients-regions, GROUP BY + HAVING, sous-requêtes corrélées ou non, requêtes multi-jointures (au moins 3 tables), et fonctions d'agrégation (AVG, COUNT, SUM, MIN, MAX).

### Key Entities

- **DonneesMeteo** : données météo par région et saison — liée à `regions` via `region_id`, contient température, humidité, précipitations, saison et date de collecte.
- **Article** : article de presse scrappé — URL unique comme clé métier, contient titre, source, résumé et dates de publication et de scraping.
- **Region** : table de référence déjà existante — sert de pivot pour le mapping ville → `region_id` dans le pipeline météo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les données des 4 régions sont collectées, transformées et insérées dans `donnees_meteo` en moins de 30 secondes par exécution complète.
- **SC-002**: Au moins 5 articles sont insérés dans `articles` à chaque première exécution du scraper sur un site disponible.
- **SC-003**: Le pipeline est idempotent : une seconde exécution ne crée pas de doublons dans `articles` et ajoute un nouvel enregistrement horodaté dans `donnees_meteo`.
- **SC-004**: Les fichiers de sauvegarde JSON sont systématiquement créés avant toute insertion en base — aucune perte de données brutes en cas d'échec de l'insertion.
- **SC-005**: Le fichier `queries.sql` contient au minimum 10 requêtes exécutables sans erreur sur la base peuplée avec les données réelles.
- **SC-006**: Aucun credential (clé API, mot de passe BDD) n'est présent dans le code source — uniquement dans `.env` (non commité).

## Assumptions

- La clé API OpenWeatherMap est obtenue par le développeur (compte gratuit suffisant pour 4 appels par exécution).
- Le site cible du scraping est un site public francophone (ex. Le Monde Santé, Ameli, ou similaire) sans barrière d'authentification ni protection anti-bot agressive.
- La table `regions` est déjà peuplée avec les 4 valeurs (southwest, southeast, northwest, northeast) par le setup de la Feature 005.
- La table `clients` est déjà peuplée avec 1 338 lignes.
- Les dossiers `data/external/api_data/` et `data/external/scraped_data/` sont créés automatiquement si absents.
- La Feature 005 (PostgreSQL setup) est entièrement déployée et fonctionnelle avant d'exécuter cette feature.
- Le scraping est limité à un site unique pour cette version — extensible à plusieurs sources ultérieurement.
