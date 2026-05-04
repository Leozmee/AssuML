# Tasks: API REST FastAPI complète

**Input**: Design documents from `/specs/007-fastapi-rest-api/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Organisation**: 4 user stories indépendantes — US1 (CRUD clients), US2 (ML scoring), US3 (contrats/sinistres), US4 (ETL + KPIs).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1 : Setup (infrastructure commune)

**Objectif** : Créer la structure du package `api/`, les dépendances et la configuration partagée.

- [X] T001 Créer les dossiers `api/routers/`, `api/schemas/` avec leurs `__init__.py` et `api/__init__.py`
- [X] T002 Vérifier que FastAPI, uvicorn, httpx, pytest-asyncio sont installés : `.venv/bin/pip install fastapi uvicorn[standard] httpx pytest-asyncio`
- [X] T003 Créer `api/dependencies.py` avec le générateur `get_db()` (yield SessionLocal, finally db.close()) réutilisé par tous les routers

---

## Phase 2 : Fondation (prérequis bloquants)

**Objectif** : Créer `api/main.py` avec le lifespan ML, le CORS, et l'inclusion de tous les routers. Créer les schémas Pydantic partagés.

- [X] T004 Créer `api/main.py` — app FastAPI avec lifespan (chargement singleton regression.pkl + classification.pkl), CORSMiddleware pour http://localhost:8501, inclusion des 7 routers avec préfixe `/api`, route /health incluse
- [X] T005 [P] Créer `api/schemas/client.py` — ClientCreate, ClientRead, ClientUpdate
- [X] T006 [P] Créer `api/schemas/prediction.py` — PredictRequest, PredictCoutResponse, PredictRisqueResponse, PredictCompletResponse
- [X] T007 [P] Créer `api/schemas/contrat.py` — ContratCreate, ContratRead, ContratUpdate
- [X] T008 [P] Créer `api/schemas/sinistre.py` — SinistreCreate, SinistreRead, SinistreUpdate
- [X] T009 [P] Créer `api/schemas/article.py` — ArticleRead, ArticleListResponse
- [X] T010 [P] Créer `api/schemas/meteo.py` — MeteoRead
- [X] T011 [P] Créer `api/routers/health.py` — GET /health : vérifie BDD + modèles ML, retourne {"status":"ok","database":"ok","models":"ok"} ou 503

**Checkpoint** : `uvicorn api.main:app --port 8000` démarre sans erreur, /docs accessible, /health retourne 200. ✅

---

## Phase 3 : US1 — CRUD clients (P1) 🎯 MVP

**Objectif** : Endpoints CRUD complets pour les clients avec pagination, soft delete et validation.

**Independent Test** : `curl http://localhost:8000/api/clients/` retourne la liste des 1 338 clients actifs.

- [X] T012 [US1] Créer `api/routers/clients.py` — router avec prefix="/api/clients" et 5 endpoints (GET liste, GET détail, POST, PUT, DELETE soft)
- [X] T013 [US1] Inclure le router clients dans `api/main.py` et vérifier via /docs que les 5 routes apparaissent
- [X] T014 [US1] Vérifier le scénario quickstart.md US1 : créer→récupérer→modifier→supprimer→vérifier liste

**Checkpoint** : Les 5 endpoints clients fonctionnent, le soft delete ne supprime pas en BDD. ✅

---

## Phase 4 : US2 — Prédictions ML (P2)

**Objectif** : Endpoints predict/cout, predict/risque, predict/complet avec orchestration business et persistance optionnelle.

**Independent Test** : POST /api/predict/complet retourne cout_predit, categorie_risque, prime, decision.

- [X] T015 [US2] Créer `api/routers/ml.py` — router avec 3 endpoints predict/cout, predict/risque, predict/complet
- [X] T016 [US2] Gérer les erreurs dans ml.py : 400 si client_id invalide, 500 si FileNotFoundError
- [X] T017 [US2] Vérifier le scénario quickstart.md US2 : prédiction anonyme puis avec client_id

**Checkpoint** : Les 3 endpoints ML fonctionnent, predict/complet persiste si client_id valide. ✅

---

## Phase 5 : US3 — Contrats et sinistres (P3)

**Objectif** : CRUD contrats et sinistres avec vérification règle métier contrat actif.

**Independent Test** : Créer un contrat, sinistre dessus, clôturer le contrat, tenter un sinistre → 400.

- [X] T018 [P] [US3] Étendre `database/crud.py` : get_contrat, get_contrats, update_contrat_statut, get_sinistres, update_sinistre_statut, get_articles, get_donnees_meteo
- [X] T019 [P] [US3] Créer `api/routers/contrats.py` — GET liste, POST créer, PUT statut
- [X] T020 [US3] Créer `api/routers/sinistres.py` — GET liste, POST avec vérification contrat actif (400 si non actif), PUT statut
- [X] T021 [US3] Vérifier le scénario quickstart.md US3 : contrat créé → sinistre créé → contrat clôturé → sinistre → 400

**Checkpoint** : La règle métier sinistre/contrat actif est enforced côté API. ✅

---

## Phase 6 : US4 — Données ETL et KPIs (P4)

**Objectif** : Endpoints lectures articles (filtre source), météo (filtres région+saison) et KPIs agrégés.

**Independent Test** : GET /api/stats/kpis retourne nb_clients_actifs=1338.

- [X] T022 [P] [US4] Créer `api/routers/articles.py` — GET /api/articles avec filtre ?source=, retourne ArticleListResponse
- [X] T023 [P] [US4] Créer `api/routers/meteo.py` — GET /api/meteo avec filtres ?region= et ?saison=
- [X] T024 [US4] Créer `api/routers/stats.py` — GET /api/stats/kpis : 5 métriques calculées en temps réel
- [X] T025 [US4] Vérifier le scénario quickstart.md US4 : articles filtrés, météo filtrée, KPIs

**Checkpoint** : L'endpoint KPIs retourne nb_clients_actifs=1338, les articles sont filtrables. ✅

---

## Phase 7 : Polish et conformité

**Objectif** : Qualité du code, vérification PEP8, test de démarrage complet.

- [X] T026 [P] Vérifier PEP8 sur le dossier api/ : `flake8 api/ --max-line-length=88` — 0 erreur
- [X] T027 [P] Vérifier que tous les routers sont bien inclus dans `api/main.py` — 23 routes exposées
- [X] T028 Vérifier le démarrage propre de l'API : uvicorn démarre, /health retourne {"status":"ok","database":"ok","models":"ok"}
- [X] T029 Créer `tests/contract/test_health.py` et `tests/contract/test_clients.py` — 8/8 tests passent

---

## Dépendances

```
T001 → T002 → T003 (séquentiels — setup)
T004 dépend de T003
T005-T011 parallèles après T001
T012 dépend de T004+T005
T015 dépend de T004+T006
T018 dépend de T001
T019-T020 dépendent de T018+T007+T008
T022-T023 dépendent de T009+T010
T024 dépend de T004
T026-T029 après toutes les implémentations
```

**User stories indépendantes** : US1, US2, US3, US4 toutes complètes ✅
