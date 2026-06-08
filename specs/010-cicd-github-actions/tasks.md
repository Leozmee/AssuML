# Tasks: CI/CD — GitHub Actions (Black, Flake8, Pytest)

**Input**: Design documents from `/specs/010-cicd-github-actions/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅
**Dépendances projet**: aucune — `black`, `flake8`, `pytest`, `pytest-asyncio`, `httpx` sont déjà
présents dans `requirements.txt` ; `database/schema.sql` contient déjà les `INSERT` de seed
pour la table `regions`.

**Organisation**: 4 stories — Qualité (P1), Tests rapides (P1), Tests d'intégration (P2),
Visibilité PR (P3). US1 et US2 sont indépendantes et peuvent être livrées comme MVP ;
US3 ajoute la couverture base de données ; US4 est purement déclarative (triggers PR).

**Tests**: Hors-scope au sens "tests automatisés du pipeline lui-même" — cette feature
*est* le dispositif de test/qualité. La validation se fait par exécution réelle du
workflow sur GitHub (cf. critères "Independent Test" de chaque story).

---

## Phase 1: Setup (Infrastructure)

**Purpose**: Préparer l'arborescence du workflow et vérifier les prérequis avant d'écrire la configuration CI.

- [ ] T001 Créer l'arborescence `.github/workflows/` à la racine du projet
- [ ] T002 Vérifier que `black>=24.0.0`, `flake8>=7.0.0`, `pytest>=8.0.0`, `pytest-asyncio>=0.23.0`, `httpx>=0.27.0` sont bien présents dans `requirements.txt` (déjà confirmé lignes 47-53 — aucune action si présent, sinon les ajouter)
- [ ] T003 Créer le secret de dépôt GitHub `CI_DB_PASSWORD` (Settings → Secrets and variables → Actions) avec une valeur de test arbitraire, distincte des vraies credentials `.env`

**Checkpoint**: Le dossier `.github/workflows/` existe, les dépendances CI sont confirmées, le secret est disponible pour le job d'intégration.

---

## Phase 2: Foundational (Prérequis bloquants)

**Purpose**: Squelette commun du workflow (déclencheurs, concurrency, structure des jobs) — nécessaire avant de remplir chaque job.

**⚠️ NOTE**: Cette phase crée le fichier `.github/workflows/ci.yml` avec son ossature
(`on:`, `concurrency:`, déclaration des 3 jobs vides). Chaque story remplit ensuite
les étapes de SON job — un seul fichier est donc partagé, les tâches qui le modifient
ne sont PAS parallélisables entre elles ([P] absent).

- [ ] T004 Créer `.github/workflows/ci.yml` avec l'en-tête : `name: CI`, déclencheurs `on.push` (toutes branches) et `on.pull_request.branches: [main]`, et `concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }` (cf. research.md décisions 6 et 7)
- [ ] T005 Ajouter dans `.github/workflows/ci.yml` la déclaration des 3 jobs vides `qualite`, `tests` et `tests-integration`, chacun avec `runs-on: ubuntu-latest` (squelette à remplir par les stories suivantes)

**Checkpoint**: `ci.yml` existe avec triggers + concurrency + 3 jobs vides ; un push de test déclenche le workflow (jobs visibles mais sans étapes).

---

## Phase 3: User Story 1 — Vérification Qualité (Black + Flake8) (Priority: P1) 🎯 MVP

**Goal**: À chaque push, le job `qualite` exécute automatiquement `black --check .` et `flake8 --max-line-length=88`, et échoue clairement si le code n'est pas conforme.

**Independent Test**: Pousser une branche avec un fichier mal formaté → le job `qualite` apparaît rouge (✗) dans l'onglet Actions, avec le détail de l'erreur Black/Flake8 dans les logs ; pousser du code conforme → le job est vert (✓) en moins de 2 minutes (SC-002).

### Implementation for User Story 1

- [ ] T006 [US1] Dans le job `qualite` de `.github/workflows/ci.yml`, ajouter les étapes `actions/checkout@v4` et `actions/setup-python@v5` (Python 3.11, `cache: 'pip'`)
- [ ] T007 [US1] Dans le job `qualite`, ajouter l'étape d'installation des dépendances (`pip install -r requirements.txt`)
- [ ] T008 [US1] Dans le job `qualite`, ajouter l'étape `black --check .` (échoue si formatage non conforme — ne reformate pas, contrairement au hook local, cf. FR-008)
- [ ] T009 [US1] Dans le job `qualite`, ajouter l'étape `flake8 --max-line-length=88` (échoue si erreurs de lint, logs au format `fichier:ligne:colonne: code`)

**Checkpoint**: Pousser une branche → le job `qualite` s'exécute seul en < 2 minutes et reflète fidèlement le résultat du hook pre-commit local pour Black/Flake8 (SC-005).

---

## Phase 4: User Story 2 — Tests unitaires et de contrat automatiques (Priority: P1) 🎯 MVP

**Goal**: À chaque push, le job `tests` exécute `pytest -m "not integration"` (tests `unit/` + `contract/`, sans base de données réelle) et rapporte précisément les échecs.

**Independent Test**: Pousser une branche avec un test unitaire en échec → le job `tests` apparaît rouge avec `FAILED tests/unit/test_xxx.py::test_yyy` dans les logs ; avec une suite verte → le job passe en moins de 5 minutes (SC-003).

### Implementation for User Story 2

- [ ] T010 [P] [US2] Dans le job `tests` de `.github/workflows/ci.yml`, ajouter les étapes `actions/checkout@v4` et `actions/setup-python@v5` (Python 3.11, `cache: 'pip'`) — identiques à T006 mais dans le job `tests` (job indépendant, fichier modifié à un autre endroit)
- [ ] T011 [US2] Dans le job `tests`, ajouter l'étape d'installation des dépendances (`pip install -r requirements.txt`) (dépend de T010 — même job)
- [ ] T012 [US2] Dans le job `tests`, ajouter l'étape `pytest -m "not integration" -v` exécutant `tests/unit/` et `tests/contract/` (utilisent SQLite in-memory / mocks — aucun service externe requis, cf. `tests/unit/test_crud.py`)

**Checkpoint**: Pousser une branche → les jobs `qualite` ET `tests` tournent en parallèle, chacun rapporte son statut indépendamment en < 5 minutes. **MVP atteint** : la CI couvre déjà l'essentiel des contrôles du hook local (hors intégration DB).

---

## Phase 5: User Story 3 — Tests d'intégration avec service PostgreSQL (Priority: P2)

**Goal**: Le job `tests-integration` démarre un conteneur PostgreSQL temporaire, y charge `database/schema.sql` (régions incluses), puis exécute `pytest -m integration` dans des conditions fidèles à l'environnement local.

**Independent Test**: Pousser une branche modifiant `database/models.py` ou `database/crud.py` → le job `tests-integration` démarre le service `postgres:15-alpine`, attend le healthcheck `pg_isready`, charge le schéma, exécute les tests d'intégration et rapporte ✓/✗ avec traces d'erreur en moins de 8 minutes (SC-004).

### Implementation for User Story 3

- [ ] T013 [US3] Dans le job `tests-integration` de `.github/workflows/ci.yml`, déclarer le `services.postgres` (image `postgres:15-alpine`, env `POSTGRES_USER: assuml_user`, `POSTGRES_PASSWORD: ${{ secrets.CI_DB_PASSWORD }}`, `POSTGRES_DB: assuml_db`, port `5432:5432`, `options` avec `--health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5`) — cf. research.md décision 3
- [ ] T014 [US3] Dans le job `tests-integration`, ajouter les étapes `actions/checkout@v4`, `actions/setup-python@v5` (Python 3.11, `cache: 'pip'`) et `pip install -r requirements.txt` (dépend de T013 — même job, mais étapes indépendantes du bloc `services`)
- [ ] T015 [US3] Dans le job `tests-integration`, ajouter une étape installant le client `postgresql-client` (`sudo apt-get install -y postgresql-client` sur le runner `ubuntu-latest`) puis chargeant le schéma : `psql -h localhost -U assuml_user -d assuml_db -f database/schema.sql` (variable `PGPASSWORD: ${{ secrets.CI_DB_PASSWORD }}`) — le DDL contient déjà les `INSERT` de seed pour `regions` (dépend de T014)
- [ ] T016 [US3] Dans le job `tests-integration`, ajouter l'étape `pytest -m integration -v` avec les variables d'environnement `DB_HOST: localhost`, `DB_PORT: 5432`, `DB_USER: assuml_user`, `DB_PASS: ${{ secrets.CI_DB_PASSWORD }}`, `DB_NAME: assuml_db` (lues par `database/connection.py` via `os.getenv`, dépend de T015)

**Checkpoint**: Pousser une branche touchant `database/` → les 3 jobs tournent (qualite, tests, tests-integration), ce dernier exécute `tests/integration/test_db_connection.py` (incluant `test_regions_preremplies`) avec un vrai PostgreSQL éphémère, en < 8 minutes.

---

## Phase 6: User Story 4 — Visibilité du statut CI sur les Pull Requests (Priority: P3)

**Goal**: Le statut des 3 jobs s'affiche directement sur toute Pull Request ouverte vers `main`, avec accès en un clic aux logs détaillés.

**Independent Test**: Ouvrir une Pull Request de `BigData` (ou toute branche) vers `main` → l'onglet "Checks" de la PR liste les 3 jobs avec leur statut individuel (✓/✗/en cours), et un clic sur "Details" ouvre les logs du job correspondant.

### Implementation for User Story 4

- [ ] T017 [US4] Vérifier que le déclencheur `on.pull_request.branches: [main]` (ajouté en T004) suffit à faire apparaître les 3 jobs comme "checks" natifs sur les PR vers `main` — aucune configuration supplémentaire requise côté workflow (l'intégration GitHub Checks est automatique dès qu'un `pull_request` déclenche les jobs)
- [ ] T018 [US4] Documenter dans `README.md` (ou section CI dédiée) la procédure de lecture des statuts CI sur une PR : où trouver l'onglet "Checks", comment ouvrir les logs d'un job en échec, et le rappel que le push n'est jamais bloqué — seule la fusion peut l'être via une règle de protection de branche (hors-scope, cf. spec.md "Hors-scope")

**Checkpoint**: Une PR ouverte vers `main` affiche les 3 checks avec liens directs vers les logs ; aucun changement de comportement sur les pushs simples (toujours non bloquants).

---

## Phase 7: Polish & Validation finale

**Purpose**: Valider que le pipeline complet reproduit fidèlement le hook pre-commit local et respecte les critères de succès mesurables de la spec.

- [ ] T019 [P] Pousser une branche de test volontairement non conforme (fichier mal formaté + test en échec + erreur de lint) et vérifier que les 3 jobs détectent chacun leur problème indépendamment, avec des logs exploitables sans reproduction locale (SC-007)
- [ ] T020 [P] Pousser une branche 100% conforme et mesurer les temps d'exécution réels des 3 jobs ; comparer aux objectifs SC-002 (< 2 min), SC-003 (< 5 min), SC-004 (< 8 min) et ajuster le cache/parallélisme si nécessaire
- [ ] T021 Comparer, sur un même commit, le résultat du hook pre-commit local et celui des jobs CI (Black, Flake8, Pytest) : confirmer 100% de cohérence local/CI (SC-005, FR-011)
- [ ] T022 Ouvrir une Pull Request réelle de `BigData` vers `main` et valider l'affichage des 3 checks + l'accès aux logs (SC-006), avant fusion ou fermeture de la PR de test

**Checkpoint final**: Les 7 critères de succès (SC-001 à SC-007) de `spec.md` sont vérifiés par l'usage réel du pipeline.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** : aucune dépendance — peut démarrer immédiatement
- **Foundational (Phase 2)** : dépend du Setup (T001) — bloque toutes les stories (le squelette `ci.yml` doit exister avant que les jobs soient remplis)
- **User Stories (Phases 3-6)** : dépendent toutes de la Phase 2 (squelette `ci.yml` + jobs vides). US1, US2 et US3 modifient chacune un job distinct du même fichier — en pratique, traiter ces blocs séquentiellement pour éviter les conflits d'édition, même si les jobs s'exécutent ensuite en parallèle sur GitHub. US4 ne nécessite que le déclencheur déjà posé en T004.
- **Polish (Phase 7)** : dépend de l'achèvement des Phases 3 à 6 — validation du pipeline complet en conditions réelles

### Story Independence at Runtime

Une fois `ci.yml` complet, les 3 jobs (`qualite`, `tests`, `tests-integration`) s'exécutent
**en parallèle** sur GitHub Actions (pas de `needs:` entre eux, cf. plan.md "Découpage en
jobs séparés") — chaque story est donc indépendamment observable et testable en production,
même si leur écriture dans le même fichier YAML impose un ordre d'édition séquentiel.

### Within Each User Story

- US1 : T006 → T007 → T008/T009 (T008 et T009 modifient des étapes différentes du même job, garder l'ordre logique Black avant Flake8 comme dans le hook local)
- US2 : T010 → T011 → T012
- US3 : T013 (déclaration service, indépendante) → T014 → T015 → T016
- US4 : T017 (vérification) → T018 (documentation, parallélisable [P] avec la plupart des autres tâches de polish)

---

## Parallel Execution Examples

```bash
# Phase 1 (Setup) — T002 et T003 sont indépendants de T001 :
Tâche: "T002 Vérifier les dépendances CI dans requirements.txt"
Tâche: "T003 Créer le secret CI_DB_PASSWORD dans les settings du dépôt GitHub"

# Phase 7 (Polish) — validations indépendantes pouvant être préparées en parallèle :
Tâche: "T019 Tester le scénario d'échec (code non conforme)"
Tâche: "T020 Mesurer les temps d'exécution sur du code conforme"
```

> **Note** : T006-T016 modifient toutes le même fichier `.github/workflows/ci.yml` — bien
> que conceptuellement organisées par story, elles doivent être éditées de façon séquentielle
> pour éviter les conflits, d'où l'absence de marqueur `[P]` sur la quasi-totalité d'entre elles.

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 — Priority P1)

1. Compléter Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1 — Qualité) → Phase 4 (US2 — Tests rapides)
2. **STOP and VALIDATE** : pousser une branche de test, vérifier que `qualite` et `tests` tournent en parallèle et reflètent fidèlement Black/Flake8/Pytest-non-intégration
3. Ce socle (T001-T012) constitue déjà une CI fonctionnelle couvrant ~80% des contrôles du hook local — livrable de manière autonome

### Incremental Delivery

1. **MVP** (US1 + US2) → CI de base opérationnelle, retour rapide sur la qualité du code et les tests métier
2. **+ US3** → ajoute la couverture des tests d'intégration PostgreSQL (le plus coûteux à mettre en place, service container + schéma)
3. **+ US4** → finalise la visibilité sur les Pull Requests (essentiellement de la vérification + documentation, peu de code)
4. **Polish** → validation globale par l'usage réel, mesure des temps, comparaison local/CI

Chaque palier est entièrement fonctionnel et démontrable indépendamment — conforme au
principe d'incréments testables de la constitution (Principe V).
