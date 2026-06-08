# Feature Specification: CI/CD — GitHub Actions (Black, Flake8, Pytest)

**Feature Branch**: `010-cicd-github-actions`
**Created**: 2026-06-08
**Status**: Draft
**Input**: User description: "Feature 10 — Mettre en place le CI/CD du projet (GitHub Actions) en s'appuyant sur les mêmes contrôles que le hook pre-commit local : Black, Flake8, Pytest"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Vérification automatique de la qualité du code à chaque push (Priority: P1)

Un développeur pousse du code sur une branche GitHub. Le pipeline CI se déclenche automatiquement et vérifie que le code respecte le formatage (Black) et les règles de style/lint (Flake8), sans qu'aucune action manuelle ne soit nécessaire.

**Why this priority**: C'est le contrôle le plus rapide et le plus fondamental — il donne un retour en quelques secondes et évite de lancer des tests plus lourds sur du code mal formaté.

**Independent Test**: Pousser une branche contenant un fichier non formaté (`black --check` doit échouer) → le job "Qualité" du workflow GitHub Actions échoue et affiche le détail de l'erreur dans les logs.

**Acceptance Scenarios**:

1. **Given** un push sur n'importe quelle branche, **When** le workflow se déclenche, **Then** le job "Qualité" exécute `black --check .` et `flake8 --max-line-length=88` automatiquement.
2. **Given** un fichier Python non conforme au formatage Black, **When** le job "Qualité" tourne, **Then** il échoue (✗) et les logs indiquent le(s) fichier(s) concerné(s).
3. **Given** un fichier Python avec une erreur Flake8 (ex: import inutilisé, ligne trop longue), **When** le job "Qualité" tourne, **Then** il échoue (✗) et les logs affichent `fichier:ligne:colonne: code erreur`.
4. **Given** tout le code respecte Black et Flake8, **When** le job "Qualité" tourne, **Then** il réussit (✓) en moins de 2 minutes.

---

### User Story 2 — Exécution automatique des tests unitaires et de contrat (Priority: P1)

Un développeur pousse du code. Le pipeline exécute automatiquement les tests qui ne nécessitent pas de base de données réelle (`tests/unit/`, `tests/contract/`), dans un environnement isolé et reproductible.

**Why this priority**: Ces tests sont rapides (pas d'infrastructure à démarrer) et couvrent la majorité de la logique métier (ML, business rules, schémas API) — ils doivent passer avant d'envisager les tests plus coûteux.

**Independent Test**: Pousser une branche avec un test unitaire qui échoue → le job "Tests" du workflow échoue et les logs identifient le test en faute (`FAILED tests/unit/test_xxx.py::test_yyy`).

**Acceptance Scenarios**:

1. **Given** un push, **When** le workflow se déclenche, **Then** le job "Tests" installe les dépendances (`requirements.txt`) puis exécute `pytest -m "not integration"`.
2. **Given** tous les tests unitaires et de contrat passent, **When** le job "Tests" se termine, **Then** il affiche ✓ avec le résumé (nombre de tests passés) en moins de 5 minutes.
3. **Given** un test échoue, **When** le job "Tests" se termine, **Then** il affiche ✗ et les logs listent les tests en échec (`FAILED`/`ERROR`) avec leur trace d'erreur.
4. **Given** aucune base de données n'est configurée dans ce job, **When** les tests s'exécutent, **Then** aucun test marqué `@pytest.mark.integration` n'est lancé (exclusion via `-m "not integration"`).

---

### User Story 3 — Exécution automatique des tests d'intégration avec une vraie base PostgreSQL (Priority: P2)

Un développeur pousse du code touchant à la couche base de données (modèles SQLAlchemy, CRUD, connexion). Le pipeline démarre un service PostgreSQL temporaire, y charge le schéma et les données de seed, puis exécute les tests d'intégration dans les mêmes conditions qu'en local.

**Why this priority**: Moins fréquent à déclencher que les tests unitaires (plus lent, infra à monter), mais indispensable pour valider que la couche `database/` fonctionne avec un vrai PostgreSQL — ce que SQLite (utilisé en tests unitaires) ne peut pas garantir.

**Independent Test**: Pousser une branche modifiant `database/models.py` ou `database/crud.py` → le job "Tests d'intégration" démarre un conteneur PostgreSQL, charge `database/schema.sql`, exécute `pytest -m integration`, et rapporte le résultat.

**Acceptance Scenarios**:

1. **Given** un push, **When** le job "Tests d'intégration" démarre, **Then** GitHub Actions lance un service container `postgres:15` avec les variables `POSTGRES_USER=assuml_user`, `POSTGRES_DB=assuml_db`, exposé sur le port 5432, et attend qu'il soit prêt (healthcheck `pg_isready`).
2. **Given** le service PostgreSQL est prêt, **When** le job poursuit, **Then** le schéma (`database/schema.sql`) et les données de seed (régions) sont chargés avant le lancement des tests.
3. **Given** la base est prête et peuplée, **When** `pytest -m integration` s'exécute, **Then** les tests se connectent via les variables d'environnement `DB_HOST=localhost`, `DB_USER`, `DB_PASS`, `DB_NAME` et passent dans les mêmes conditions qu'en local.
4. **Given** un test d'intégration échoue (ex: schéma désynchronisé), **When** le job se termine, **Then** il affiche ✗ avec la trace d'erreur, sans bloquer les autres jobs déjà terminés.

---

### User Story 4 — Visibilité du statut CI sur les Pull Requests vers `main` (Priority: P3)

Un développeur ouvre une Pull Request vers `main`. Le statut de chaque job CI (Qualité, Tests, Tests d'intégration) s'affiche directement sur la PR, lui permettant de décider en connaissance de cause s'il fusionne ou corrige d'abord.

**Why this priority**: Confort et traçabilité — ne bloque rien techniquement par défaut, mais structure la prise de décision de fusion. Peut être complété plus tard par une règle de protection de branche (hors-scope de cette feature).

**Independent Test**: Ouvrir une PR de `BigData` vers `main` → les 3 jobs apparaissent dans l'onglet "Checks" de la PR avec leur statut individuel (✓/✗/en cours).

**Acceptance Scenarios**:

1. **Given** une Pull Request est ouverte vers `main`, **When** le workflow se déclenche, **Then** les 3 jobs (Qualité, Tests, Tests d'intégration) apparaissent comme "checks" sur la PR avec leur statut respectif.
2. **Given** un ou plusieurs jobs sont rouges (✗), **When** le développeur consulte la PR, **Then** il peut cliquer sur "Details" pour ouvrir directement les logs du job en échec.
3. **Given** tous les jobs sont verts (✓), **When** le développeur consulte la PR, **Then** un résumé "All checks have passed" s'affiche.

---

### Edge Cases

- Que se passe-t-il si `black`, `flake8` ou `pytest` ne sont pas listés dans `requirements.txt` ? → Le job échoue à l'étape d'installation avec un message clair (`command not found`), il faut les ajouter aux dépendances avant le premier run.
- Que se passe-t-il si le service PostgreSQL met plus de temps que prévu à démarrer ? → Le healthcheck `pg_isready` fait patienter le job jusqu'à disponibilité (avec un nombre de tentatives limité avant timeout).
- Que se passe-t-il si un test d'intégration nécessite des données de seed absentes du schéma chargé en CI ? → Le test échoue de façon explicite (ex: `assert count == 4` sur la table `regions`) ; il faut s'assurer que le script de chargement reproduit fidèlement l'état attendu.
- Que se passe-t-il si plusieurs pushs successifs sont effectués rapidement sur la même branche ? → GitHub Actions annule automatiquement les exécutions précédentes obsolètes via la concurrency (à configurer) pour éviter de gaspiller des minutes CI.
- Que se passe-t-il si le projet ne contient pas (encore) de `Dockerfile`/`docker-compose.yml` ? → Aucun job de build/déploiement Docker n'est inclus dans cette feature (CD hors-scope) ; uniquement la CI (Qualité + Tests).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le système DOIT déclencher automatiquement un workflow GitHub Actions à chaque `push` sur n'importe quelle branche et à chaque ouverture/mise à jour de Pull Request vers `main`.
- **FR-002**: Le workflow DOIT exécuter `black --check .` sur le code source et échouer si un fichier n'est pas conforme au formatage attendu.
- **FR-003**: Le workflow DOIT exécuter `flake8 --max-line-length=88` sur le code source et échouer si une règle de style/lint est violée.
- **FR-004**: Le workflow DOIT exécuter `pytest -m "not integration"` (tests unitaires + contrats) dans un environnement sans base de données externe.
- **FR-005**: Le workflow DOIT démarrer un service container PostgreSQL 15, charger le schéma (`database/schema.sql`) et les données de seed nécessaires, puis exécuter `pytest -m integration`.
- **FR-006**: Le workflow DOIT séparer ces contrôles en jobs indépendants (Qualité, Tests, Tests d'intégration) afin d'obtenir un retour rapide dès qu'un problème de formatage/lint est détecté, sans attendre les tests plus longs.
- **FR-007**: Le workflow DOIT afficher le statut (✓/✗) de chaque job directement sur la Pull Request via l'intégration native GitHub Checks.
- **FR-008**: Le workflow NE DOIT PAS modifier ou reformater le code automatiquement (contrairement au hook pre-commit local) — il doit seulement rapporter les non-conformités.
- **FR-009**: Le workflow DOIT mettre en cache les dépendances Python (`pip`) entre les exécutions afin de réduire le temps d'exécution.
- **FR-010**: Le workflow DOIT annuler les exécutions précédentes obsolètes lors de pushs successifs rapprochés sur la même branche (concurrency groups).
- **FR-011**: Le pipeline CI DOIT reproduire fidèlement les contrôles déjà appliqués localement par le hook pre-commit (`/Users/leogallus/.git-hooks/pre-commit` : Black, Flake8, Pytest), garantissant la cohérence entre environnement local et CI.

### Hors-scope (explicitement exclu de cette feature)

- La partie **CD** (Continuous Delivery/Deployment) — build et publication d'images Docker — est hors-scope : aucun `Dockerfile`/`docker-compose.yml` n'existe encore dans le repo. Elle pourra faire l'objet d'une feature ultérieure une fois l'image définie.
- La mise en place de **règles de protection de branche** (`branch protection rules` bloquant la fusion si la CI est rouge) est hors-scope technique de cette feature (configuration GitHub côté repo, pas du code) — elle peut être activée manuellement par le mainteneur une fois le workflow validé.
- Le déploiement vers un environnement de production/démo est hors-scope.

### Key Entities *(include if feature involves data)*

- **Workflow GitHub Actions** : fichier de configuration déclaratif (`.github/workflows/ci.yml`) décrivant les déclencheurs, jobs et étapes du pipeline.
- **Job** : unité d'exécution indépendante du workflow (Qualité, Tests, Tests d'intégration), avec son propre environnement et ses propres étapes.
- **Service container PostgreSQL** : conteneur Docker temporaire démarré par GitHub Actions le temps du job "Tests d'intégration", peuplé avec le schéma et les données de seed du projet.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: À chaque push, le workflow se déclenche automatiquement sans intervention manuelle, et le statut de chaque job est visible dans l'onglet "Actions" en moins d'une minute après le push.
- **SC-002**: Le job "Qualité" (Black + Flake8) se termine en moins de 2 minutes.
- **SC-003**: Le job "Tests" (unitaires + contrats) se termine en moins de 5 minutes.
- **SC-004**: Le job "Tests d'intégration" (avec service PostgreSQL) se termine en moins de 8 minutes, schéma et seed inclus.
- **SC-005**: 100% des contrôles qui passent localement via le hook pre-commit (Black, Flake8, Pytest) produisent le même résultat (✓/✗) en CI — aucune divergence local/CI.
- **SC-006**: Le statut des 3 jobs est visible directement sur toute Pull Request ouverte vers `main`, avec accès en un clic aux logs détaillés en cas d'échec.
- **SC-007**: Un développeur qui reçoit un job rouge peut identifier la cause exacte (fichier, ligne, test en échec) uniquement à partir des logs affichés, sans avoir à reproduire le problème en local pour comprendre où il se situe.

## Assumptions

- `black`, `flake8` et `pytest` (déjà utilisés par le hook pre-commit local) seront ajoutés à `requirements.txt` (ou un `requirements-dev.txt` séparé) afin d'être installables en CI.
- Le schéma PostgreSQL (`database/schema.sql`) et les données de seed existantes (ex: les 4 régions attendues par `tests/integration/test_db_connection.py`) sont suffisants pour reproduire l'état attendu par les tests d'intégration.
- Les credentials utilisés par le service PostgreSQL en CI sont des valeurs de test arbitraires (ex: `assuml_user` / mot de passe généré), stockées comme variables/secrets du workflow — jamais les vraies credentials de production.
- Le projet reste mono-version Python 3.11 — pas besoin de matrice multi-versions pour cette feature.
- La création de `Dockerfile`/`docker-compose.yml` (mentionnée dans la constitution comme tech CI/CD) est traitée dans une feature séparée ; cette spec couvre uniquement la CI (qualité + tests).
