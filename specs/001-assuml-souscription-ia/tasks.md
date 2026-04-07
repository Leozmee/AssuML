---

description: "Liste de tâches — AssuML Système de Souscription Assurance Santé IA"
---

# Tasks: AssuML — Système de Souscription Assurance Santé IA

**Input**: Documents de conception dans `specs/001-assuml-souscription-ia/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Inclus — requis par la constitution (Principe V) et par SC-004/SC-006 de la spec.

**Organisation**: Tâches groupées par User Story pour permettre une implémentation
et une validation indépendante de chaque fonctionnalité.

## Format: `[ID] [P?] [Story?] Description — fichier/cible`

- **[P]**: Peut s'exécuter en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User Story concernée (US1…US8)
- Les chemins de fichiers sont relatifs à la racine du dépôt

---

## Phase 1 : Setup (Infrastructure partagée)

**But**: Initialiser la structure du projet, la configuration et la containerisation.

- [ ] T001 Créer la structure de répertoires complète du projet (data/, ml_models/, business/, data_pipeline/, api/, streamlit_app/, database/, tests/, monitoring/)
- [ ] T002 Créer `requirements.txt` avec toutes les dépendances (fastapi, uvicorn, pydantic, sqlalchemy, psycopg2-binary, streamlit, plotly, scikit-learn, pandas, numpy, joblib, duckdb, beautifulsoup4, requests, prometheus-client, pytest, httpx, flake8, black)
- [ ] T003 [P] Créer `.env.example` avec DATABASE_URL, OPENWEATHER_API_KEY, PYTHONPATH
- [ ] T004 [P] Créer `.gitignore` incluant `.env`, `*.pkl`, `*.parquet`, `__pycache__/`, `.pytest_cache/`, `data/big_data/`, `ml_models/saved_models/`
- [ ] T005 [P] Créer `Dockerfile.api` (Python 3.11-slim, port 8000, uvicorn)
- [ ] T006 [P] Créer `Dockerfile.streamlit` (Python 3.11-slim, port 8501, streamlit run)
- [ ] T007 [P] Créer `docker-compose.yml` avec services : db (postgres:15), api, streamlit, prometheus, grafana — réseau Docker interne, variables d'env depuis `.env`

---

## Phase 2 : Fondation (Prérequis bloquants)

**But**: Base de données, ORM et API skeleton — DOIT être complète avant tout User Story.

**⚠️ CRITIQUE**: Aucun travail sur les User Stories ne peut commencer avant cette phase.

- [ ] T008 Créer `database/schema.sql` avec les 7 tables (regions, clients, predictions, contrats, sinistres, donnees_meteo, articles), 5 FK ON DELETE CASCADE, 22 contraintes CHECK (age 18-120, imc 10-80, score_risque 0-1, montant_sinistre > 0, etc.), 20 index, INSERT INTO regions pour les 4 valeurs
- [ ] T009 [P] Créer `api/database.py` : connexion SQLAlchemy (create_engine, SessionLocal, Base, get_db dependency)
- [ ] T010 [P] Créer `api/main.py` : application FastAPI avec CORS, inclusion des routers, endpoint `/health`, middleware Prometheus (`/metrics`)
- [ ] T011 [P] Créer `api/models/region.py` : modèle SQLAlchemy Region
- [ ] T012 [P] Créer `api/models/client.py` : modèle SQLAlchemy Client avec toutes les colonnes et relations
- [ ] T013 [P] Créer `api/models/prediction.py` : modèle SQLAlchemy Prediction
- [ ] T014 [P] Créer `api/models/contrat.py` : modèle SQLAlchemy Contrat
- [ ] T015 [P] Créer `api/models/sinistre.py` : modèle SQLAlchemy Sinistre
- [ ] T016 [P] Créer `api/models/donnee_meteo.py` : modèle SQLAlchemy DonneeMeteo
- [ ] T017 [P] Créer `api/models/article.py` : modèle SQLAlchemy Article
- [ ] T018 [P] Créer `streamlit_app/app.py` : point d'entrée Streamlit avec navigation multipage et configuration de la sidebar
- [ ] T019 [P] Créer `monitoring/prometheus.yml` : configuration scrape FastAPI (`http://api:8000/metrics`, interval 15s)

**Checkpoint**: Base de données initialisée + API skeleton fonctionnel → les User Stories peuvent commencer.

---

## Phase 3 : User Story 1 — Gestion CRUD Clients (Priority: P1) 🎯 MVP

**But**: Permettre la création, consultation, modification et suppression logique de clients.

**Test indépendant**: Créer un client via l'API, le retrouver dans la liste, modifier son IMC,
le soft-supprimer, vérifier qu'il disparaît des listes actives mais reste en base.

### Tests pour US1

- [ ] T020 [P] [US1] Créer `tests/integration/test_clients_api.py` : tests POST /api/clients (nominal + validation), GET /api/clients (liste + filtres), GET /api/clients/{id} (trouvé + 404), PUT /api/clients/{id}, DELETE /api/clients/{id} (soft delete vérifié en base)
- [ ] T021 [P] [US1] Créer `tests/unit/test_schemas_clients.py` : tests Pydantic (champs manquants, IMC hors plage, âge hors plage, région invalide)

### Implémentation US1

- [ ] T022 [P] [US1] Créer `api/schemas/client.py` : schémas Pydantic ClientCreate (obligatoires), ClientRead (avec relations), ClientUpdate (tous optionnels), ClientListResponse
- [ ] T023 [US1] Créer `api/routers/clients.py` : GET /api/clients (avec filtres region, fumeur, categorie_risque, limit, offset), GET /api/clients/{id}, POST /api/clients (→ 201), PUT /api/clients/{id} (→ 200), DELETE /api/clients/{id} (soft delete via date_suppression = NOW())
- [ ] T024 [US1] Créer `api/routers/stats.py` : GET /api/stats/kpis (total clients actifs, contrats actifs, sinistres en cours, répartition risque, coût moyen prédit)
- [ ] T025 [US1] Créer `streamlit_app/pages/3_crud.py` : formulaire création client (st.form), liste clients avec filtres (st.selectbox), édition via API PUT, soft delete via API DELETE — toutes les requêtes passent par `requests` vers l'API FastAPI

**Checkpoint**: US1 entièrement fonctionnelle et testable indépendamment.

---

## Phase 4 : User Story 2 — Scoring IA (Priority: P1) 🎯 MVP

**But**: Prédire le coût médical, classifier le risque, calculer la prime et la décision.

**Test indépendant**: Soumettre un profil (age=45, fumeur=True, imc=32, région=northeast)
via POST /api/predict/complet → obtenir cout_predit, categorie_risque=eleve,
decision=examiner, prime calculée, résultat persisté en base avec version_modele.

### Exploration et entraînement ML

- [ ] T026 Créer `notebooks/exploration.ipynb` : chargement insurance.csv, EDA complet (distribution charges, corrélations, impact fumeur/IMC/age), encodage (smoker yes→1, sex female→1, region one-hot drop_first), comparaison LinearRegression vs RandomForestRegressor vs GradientBoostingRegressor (R², MAE, RMSE), sélection du meilleur algorithme
- [ ] T027 Créer `ml_models/training/train_regression.py` : pipeline sklearn (StandardScaler + RandomForestRegressor), train_test_split(test_size=0.3, random_state=42), calcul R²/MAE/RMSE train et test, sauvegarde `ml_models/saved_models/regression.pkl` et `metadata.json`
- [ ] T028 Créer `ml_models/training/train_classification.py` : création target categorie_risque (faible/moyen/eleve/critique), pipeline sklearn (RandomForestClassifier), calcul accuracy/F1/matrice de confusion, sauvegarde `ml_models/saved_models/classification.pkl` et mise à jour `metadata.json`

### Logique ML et métier

- [ ] T029 [P] [US2] Créer `ml_models/prediction/predict.py` : chargement unique des .pkl au module load, `predict_cost(age, sexe, imc, enfants, fumeur, region) → float`, `predict_risk(age, sexe, imc, enfants, fumeur, region) → (categorie_risque: str, score_risque: float)`
- [ ] T030 [P] [US2] Créer `business/risk_engine.py` : `get_categorie_risque(cout_predit) → str`, `get_decision(categorie_risque) → str`, constantes de seuils (5000, 15000, 30000)
- [ ] T031 [P] [US2] Créer `business/scoring.py` : `calculate_prime(cout_predit, categorie_risque) → float` (coefficients : faible=1.0, moyen=1.15, eleve=1.35, critique=1.60)

### Tests US2

- [ ] T032 [P] [US2] Créer `tests/unit/test_predict.py` : tests predict_cost (profil fumeur vs non-fumeur, range des valeurs), tests predict_risk (catégories retournées, score entre 0 et 1)
- [ ] T033 [P] [US2] Créer `tests/unit/test_scoring.py` : tests calculate_prime (coefficients par catégorie), tests get_decision (mapping catégorie→décision)
- [ ] T034 [P] [US2] Créer `tests/integration/test_predictions_api.py` : tests POST /api/predict/cout, POST /api/predict/risque, POST /api/predict/complet (avec et sans client_id, validation persistance)

### API et UI US2

- [ ] T035 [P] [US2] Créer `api/schemas/prediction.py` : PredictRequest, PredictCoutResponse, PredictRisqueResponse, PredictCompletResponse
- [ ] T036 [US2] Créer `api/routers/predictions.py` : POST /api/predict/cout, POST /api/predict/risque, POST /api/predict/complet (appel predict.py + scoring.py + risk_engine.py, persistance optionnelle si client_id fourni), GET /api/predictions (liste avec filtres)
- [ ] T037 [US2] Créer `streamlit_app/pages/1_scoring.py` : formulaire profil client (st.form avec tous les champs), bouton "Scorer", affichage résultat (coût, catégorie risque avec couleur, prime, décision avec badge), historique des dernières prédictions via API GET /api/predictions

**Checkpoint**: US1 + US2 fonctionnelles — MVP complet (CRUD client + scoring IA).

---

## Phase 5 : User Story 3 — Gestion des Contrats (Priority: P2)

**But**: Créer et gérer les contrats d'assurance pour les clients acceptés.

**Test indépendant**: Créer un contrat pour un client existant via POST /api/contrats,
vérifier statut=actif, modifier le statut en résilié via PUT /api/contrats/{id}.

### Tests US3

- [ ] T038 [P] [US3] Créer `tests/integration/test_contrats_api.py` : tests POST /api/contrats (nominal, client inexistant → 404), GET /api/contrats (filtre client_id, filtre statut), PUT /api/contrats/{id} (changement statut)

### Implémentation US3

- [ ] T039 [P] [US3] Créer `api/schemas/contrat.py` : ContratCreate, ContratRead, ContratUpdate, ContratListResponse
- [ ] T040 [US3] Créer `api/routers/contrats.py` : GET /api/contrats (filtres client_id, statut), POST /api/contrats (→ 201, statut=actif par défaut), PUT /api/contrats/{id} (mise à jour statut et/ou date_fin)
- [ ] T041 [US3] Ajouter section "Contrats" dans `streamlit_app/pages/3_crud.py` : onglet ou section dédiée pour lister les contrats d'un client sélectionné (GET /api/contrats?client_id=X), créer un contrat (POST), résilier (PUT statut=résilié)

**Checkpoint**: US1 + US2 + US3 fonctionnelles — CRUD client + scoring + gestion contrats.

---

## Phase 6 : User Story 4 — Déclaration des Sinistres (Priority: P2)

**But**: Déclarer et suivre les sinistres sur les contrats actifs.

**Test indépendant**: Déclarer un sinistre (maladie, 1500€) sur un contrat actif →
statut en_cours. Tenter de déclarer sur un contrat résilié → erreur 400.

### Tests US4

- [ ] T042 [P] [US4] Créer `tests/integration/test_sinistres_api.py` : tests POST /api/sinistres (contrat actif ✅, contrat résilié → 400, montant nul → 422), GET /api/sinistres (filtres), PUT /api/sinistres/{id} (mise à jour statut)

### Implémentation US4

- [ ] T043 [P] [US4] Créer `api/schemas/sinistre.py` : SinistreCreate, SinistreRead, SinistreUpdate, SinistreListResponse
- [ ] T044 [US4] Créer `api/routers/sinistres.py` : GET /api/sinistres (filtres contrat_id, statut_sinistre), POST /api/sinistres (vérification contrat.statut == 'actif' → sinon 400), PUT /api/sinistres/{id} (mise à jour statut_sinistre)
- [ ] T045 [US4] Ajouter section "Sinistres" dans `streamlit_app/pages/3_crud.py` : liste sinistres d'un contrat sélectionné, formulaire déclaration sinistre (type, montant, description, date), mise à jour statut

**Checkpoint**: US1–US4 fonctionnelles — cycle de vie complet assurance.

---

## Phase 7 : User Story 5 — Analytics Big Data (Priority: P2)

**But**: Visualiser 10 M lignes de données via DuckDB + Plotly Express en moins de 5 s.

**Test indépendant**: Ouvrir le module Analytics, appliquer filtre "fumeurs",
voir 5 graphiques interactifs se mettre à jour en < 5 secondes.

### Génération des données

- [ ] T046 Créer `data_pipeline/generate_synthetic.py` : génération de 10 M lignes synthétiques basées sur les distributions de insurance.csv (age, sex, bmi, children, smoker, region, charges), calcul de colonnes dérivées (charges_log, age_group, bmi_category, risk_score), sauvegarde en `data/big_data/insurance_big.parquet`

### Implémentation US5

- [ ] T047 [P] [US5] Créer module DuckDB réutilisable `streamlit_app/analytics_db.py` : connexion DuckDB, exécution de requêtes paramétrées sur `data/big_data/insurance_big.parquet`, gestion du cas fichier absent (message d'indisponibilité)
- [ ] T048 [US5] Créer `streamlit_app/pages/2_analytics.py` : filtres interactifs (st.multiselect région, st.selectbox fumeur, st.select_slider âge), 5 graphiques Plotly Express (distribution coûts px.histogram, répartition régionale px.bar, impact tabagisme px.box, corrélation âge/coût px.scatter, corrélation IMC/coût px.scatter), appel DuckDB direct (pas via API)

**Checkpoint**: US1–US5 fonctionnelles — 5 fonctionnalités démontrables indépendamment.

---

## Phase 8 : User Story 6 — Actualités Assurance (Priority: P3)

**But**: Scraper et afficher des articles d'actualité assurance/santé.

**Test indépendant**: Exécuter le scraper, vérifier des articles en base (table articles),
ouvrir le module Actualités et voir ≥ 5 articles avec titre, source et résumé.

### ETL Scraping

- [ ] T049 [P] [US6] Créer `data_pipeline/extract/scraper.py` : scraping BeautifulSoup + Requests sur ≥ 1 source publique (ex. argus.fr ou assurance.com), extraction titre/URL/résumé/date, sauvegarde brute dans `data/external/scraped_data/articles_raw.json`
- [ ] T050 [P] [US6] Créer `data_pipeline/transform/transform_articles.py` : nettoyage HTML, déduplication par URL, normalisation des dates, formatage conforme au schéma de la table articles
- [ ] T051 [US6] Mettre à jour `data_pipeline/load/db_loader.py` : insertion articles en base (INSERT OR IGNORE sur url_source unique)

### API et UI US6

- [ ] T052 [P] [US6] Créer `api/schemas/donnees_externes.py` : ArticleRead, ArticleListResponse (+ MétéoRead, MétéoListResponse réutilisés en US7)
- [ ] T053 [P] [US6] Créer `api/routers/articles.py` : GET /api/articles (filtres nom_source, depuis, limit, offset)
- [ ] T054 [US6] Créer `streamlit_app/pages/5_actualites.py` : liste d'articles via GET /api/articles (st.expander par article : titre, source, date, résumé, lien externe), filtre par source (st.selectbox), gestion mode dégradé si API indisponible

**Checkpoint**: US6 fonctionnelle — source de données scraping démontrée.

---

## Phase 9 : User Story 7 — Météo par Région (Priority: P3)

**But**: Collecter et afficher les données météo OpenWeatherMap par région.

**Test indépendant**: Exécuter l'extracteur météo, vérifier 4 entrées en base (une par région),
afficher température/humidité/précipitations pour chaque région dans Streamlit.

### ETL Météo

- [ ] T055 [P] [US7] Créer `data_pipeline/extract/api_extractor.py` : appel OpenWeatherMap pour 4 villes US représentatives (Phoenix=southwest, Atlanta=southeast, Seattle=northwest, Boston=northeast), clé API depuis `.env`, sauvegarde JSON dans `data/external/api_data/`
- [ ] T056 [P] [US7] Créer `data_pipeline/transform/transform_meteo.py` : extraction temperature_moy, humidite_moy, precipitations, détermination saison depuis date_collecte
- [ ] T057 [US7] Mettre à jour `data_pipeline/load/db_loader.py` : insertion données météo en base (table donnees_meteo)

### API et UI US7

- [ ] T058 [P] [US7] Créer `api/routers/meteo.py` : GET /api/meteo (filtres region, saison)
- [ ] T059 [US7] Ajouter section "Météo par région" dans `streamlit_app/pages/2_analytics.py` : tableau comparatif des 4 régions (température, humidité, précipitations) via GET /api/meteo, graphique Plotly comparaison régionale

**Checkpoint**: US7 fonctionnelle — source de données API externe démontrée.

---

## Phase 10 : User Story 8 — Monitoring ML & Infrastructure (Priority: P3)

**But**: Monitorer les performances des modèles ML et l'infrastructure via Prometheus/Grafana.

**Test indépendant**: Ouvrir le module Monitoring, voir R²/MAE/RMSE du modèle régression
et accuracy/F1 de la classification avec indicateur vert/orange/rouge. Vérifier
que `/metrics` expose les compteurs de prédictions par catégorie.

### Prometheus et métriques ML

- [ ] T060 [P] [US8] Ajouter dans `api/main.py` : instrumentation Prometheus (Counter http_requests_total, Histogram http_request_duration_seconds, Gauge ml_model_r2_score, Counter ml_predictions_total par catégorie), exposition endpoint `/metrics` via prometheus-client
- [ ] T061 [P] [US8] Créer `monitoring/grafana/dashboards/assuml.json` : dashboard Grafana avec panneaux (requests/s, p95 latency, CPU/mémoire, prédictions par catégorie)

### UI Monitoring

- [ ] T062 [US8] Créer `streamlit_app/pages/4_monitoring.py` :
  - Section "Modèles ML" : lecture `ml_models/saved_models/metadata.json`, affichage R²/MAE/RMSE (régression) et accuracy/F1/matrice de confusion (classification), indicateur vert (✅) si au-dessus des seuils (R² ≥ 0.70, accuracy ≥ 0.80), orange sinon
  - Section "Infrastructure" : récupération métriques Prometheus GET http://prometheus:9090/api/v1/query, affichage disponibilité API, temps de réponse moyen, nb prédictions par catégorie

**Checkpoint**: US1–US8 toutes fonctionnelles — 21 compétences couvertes.

---

## Phase finale : Polish & Transversal

**But**: CI/CD, tests complets, documentation et validation finale.

- [ ] T063 Créer `.github/workflows/ci.yml` : 3 jobs séquentiels — lint (flake8 --max-line-length=88 + black --check), tests (pytest tests/ avec base PostgreSQL en service Docker), build Docker (docker build Dockerfile.api + Dockerfile.streamlit)
- [ ] T064 [P] Créer `tests/contract/test_api_contracts.py` : vérification de la structure de réponse de chaque endpoint (champs présents, types corrects) via httpx
- [ ] T065 [P] Créer `tests/unit/test_risk_engine.py` : tests get_categorie_risque (seuils aux limites 4999, 5000, 14999, 15000, 29999, 30000), tests get_decision (mapping complet)
- [ ] T066 [P] Créer `data_pipeline/extract/csv_extractor.py` : lecture `data/small_data/insurance.csv`, validation des colonnes requises, retour DataFrame Pandas
- [ ] T067 [P] Vérifier et compléter les docstrings en français dans tous les fichiers Python (api/routers/, ml_models/prediction/, business/)
- [ ] T068 [P] Vérifier la conformité flake8 + black sur l'ensemble du projet (`flake8 . --max-line-length=88 && black .`)
- [ ] T069 Exécuter le quickstart.md de bout en bout (init BDD → ML → ETL → API → Streamlit → smoke tests) et corriger les écarts
- [ ] T070 [P] Créer `data_pipeline/load/db_loader.py` (si non créé) : fonctions génériques d'insertion pour chaque table, gestion des doublons, logging en français

---

## Dépendances et ordre d'exécution

### Dépendances entre phases

- **Phase 1 (Setup)** : Aucune dépendance — démarre immédiatement.
- **Phase 2 (Fondation)** : Dépend de Phase 1 — BLOQUE toutes les User Stories.
- **US1 (Phase 3)** : Dépend de Phase 2 — peut démarrer seule.
- **US2 (Phase 4)** : Dépend de Phase 2 — indépendante de US1 mais ML à entraîner d'abord (T026-T028).
- **US3 (Phase 5)** : Dépend de US1 (clients en base) et Phase 2.
- **US4 (Phase 6)** : Dépend de US3 (contrats en base).
- **US5 (Phase 7)** : Dépend de Phase 1 uniquement (pas de PostgreSQL) — peut s'exécuter très tôt.
- **US6 (Phase 8)** : Dépend de Phase 2 (table articles).
- **US7 (Phase 9)** : Dépend de Phase 2 (table donnees_meteo).
- **US8 (Phase 10)** : Dépend de US2 (modèles ML entraînés, metadata.json) et Phase 2 (API).
- **Polish (Phase finale)** : Dépend de toutes les User Stories souhaitées.

### Dépendances intra-US2 (scoring IA — ordre strict)

1. T026 (notebook EDA) → T027 (train_regression) → T028 (train_classification)
2. T027 + T028 terminés → T029 (predict.py)
3. T029 terminé → T036 (router predictions)

### Opportunités de parallélisme

- **Phase 2** : T009 à T019 peuvent tous se lancer en parallèle (fichiers distincts).
- **US1** : T020 et T021 (tests) en parallèle + T022 (schemas) en parallèle ; T023 après T022.
- **US2** : T029, T030, T031, T032, T033 en parallèle après T028.
- **US5** : T047 et T046 en parallèle ; T048 après T047.
- **US6** : T049, T050 en parallèle ; T051 après T050 ; T052, T053 en parallèle après T051.
- **Polish** : T063 à T068 peuvent s'exécuter en parallèle.

---

## Exemples de parallélisme

### Phase 2 (Fondation) — tout en parallèle

```bash
# Lancer simultanément :
Task: "Créer api/database.py"                  # T009
Task: "Créer api/main.py"                      # T010
Task: "Créer api/models/region.py"             # T011
Task: "Créer api/models/client.py"             # T012
Task: "Créer api/models/prediction.py"         # T013
Task: "Créer streamlit_app/app.py"             # T018
Task: "Créer monitoring/prometheus.yml"        # T019
```

### US2 après entraînement ML

```bash
# Après T028 (classification entraînée), lancer simultanément :
Task: "Créer ml_models/prediction/predict.py"  # T029
Task: "Créer business/risk_engine.py"          # T030
Task: "Créer business/scoring.py"              # T031
Task: "Créer tests/unit/test_predict.py"       # T032
Task: "Créer tests/unit/test_scoring.py"       # T033
```

---

## Stratégie d'implémentation

### MVP First (US1 + US2 uniquement)

1. Compléter Phase 1 (Setup)
2. Compléter Phase 2 (Fondation)
3. Compléter US2 Phase 4 — entraînement ML (T026-T028) **en priorité** (le plus long)
4. Compléter US1 Phase 3 **en parallèle** si possible
5. **STOP et VALIDATION** : smoke test CRUD client + scoring complet
6. Démo MVP : créer client → scorer → obtenir décision

### Livraison incrémentale (semaines 1-8)

| Semaines | Phases | Livrable démontrable |
|----------|--------|----------------------|
| S1-S2 | Phase 1 + 2 + US2 (ML) | Notebooks EDA + modèles .pkl |
| S3-S4 | US1 + US3 + US4 + ETL sources | CRUD complet + cycle de vie assurance |
| S5-S6 | US2 (API+UI) + US5 + US6 + US7 | Système complet avec analytics + sources |
| S7 | US8 + CI/CD | Monitoring + pipeline automatisé |
| S8 | Polish + Tests | Validation 21 compétences + soutenance |

### Stratégie parallèle (en solo — travailler sur des fichiers différents)

- Lancer l'entraînement ML (T026-T028) en tâche de fond pendant qu'on travaille sur le schéma BDD (T008) ou les modèles SQLAlchemy (T011-T017).
- Une fois les .pkl générés, US2 API/UI et US1 peuvent avancer simultanément.

---

## Notes

- `[P]` = fichiers différents, pas de dépendances — peuvent s'exécuter en parallèle
- `[USn]` = traçabilité vers la User Story correspondante dans spec.md
- Chaque User Story est indépendamment testable et déployable
- Tous les commits doivent passer flake8 + black avant push
- Les fichiers `.pkl` et `.parquet` ne doivent JAMAIS être commités
- Le soft delete est TOUJOURS préféré au DELETE physique (constitution RGPD)
