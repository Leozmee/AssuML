# Implementation Plan: CI/CD — GitHub Actions (Black, Flake8, Pytest)

**Branch**: `010-cicd-github-actions` | **Date**: 2026-06-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-cicd-github-actions/spec.md`

## Summary

Mettre en place un workflow GitHub Actions (`.github/workflows/ci.yml`) qui reproduit,
sur les serveurs GitHub et à chaque push / Pull Request, les contrôles déjà appliqués
localement par le hook pre-commit (`Black`, `Flake8`, `Pytest`). Le pipeline est découpé
en 3 jobs indépendants — Qualité, Tests, Tests d'intégration — afin de donner un retour
rapide en cas d'erreur de formatage/lint avant de lancer les tests plus coûteux
(notamment ceux nécessitant un vrai PostgreSQL).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies (CI)**: black, flake8, pytest, pytest-asyncio, httpx (déjà utilisés en local/tests)
**CI Platform**: GitHub Actions (`ubuntu-latest`)
**Storage (job intégration)**: service container `postgres:15` éphémère — détruit en fin de job
**Testing**: réutilise la suite existante (`tests/unit`, `tests/contract`, `tests/integration`) sans rien y ajouter
**Target Platform**: Workflow déclenché sur push (toutes branches) + Pull Request vers `main`
**Project Type**: Configuration CI déclarative (YAML), aucune modification du code applicatif
**Performance Goals**: Job Qualité < 2 min, Job Tests < 5 min, Job Intégration < 8 min (cf. SC-002 à SC-004)
**Constraints**: ne doit rien modifier/committer automatiquement (contrairement au hook local qui reformate) ; ne doit pas exposer de vrais credentials (valeurs de test uniquement)
**Scale/Scope**: 1 fichier de workflow, 3 jobs, aucun changement de code applicatif

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Status | Justification |
| -------- | ------ | ------------- |
| I — Trois sources de données | ✅ | N/A — feature d'infrastructure CI, ne touche à aucune source de données |
| II — ML rigoureux et traçable | ✅ | N/A — aucun modèle ML concerné ; les tests ML existants (`tests/unit/test_regression.py`, `test_classification.py`) sont simplement exécutés tels quels |
| III — Séparation stricte des couches | ✅ | Le workflow n'introduit aucun appel direct entre couches ; il se contente d'exécuter les suites de tests existantes qui respectent déjà cette séparation |
| IV — RGPD et sécurité | ✅ | Les credentials PostgreSQL utilisés en CI sont des valeurs de test stockées en variables/secrets GitHub (jamais les vraies credentials `.env` de prod) ; aucune donnée réelle n'est exposée |
| V — Qualité, testabilité, documentation | ✅ | Le but même de cette feature est de renforcer la qualité (Black/Flake8/Pytest exécutés systématiquement) ; le workflow YAML est commenté en français |

**Aucune violation — feu vert pour l'implémentation.**

## Project Structure

### Documentation (this feature)

```text
specs/010-cicd-github-actions/
├── plan.md              ← ce fichier
├── research.md          ← Phase 0 (décisions techniques : triggers, jobs, service container)
├── checklists/
│   └── requirements.md  ← créé par /speckit-specify
└── spec.md
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── ci.yml            # Workflow unique : 3 jobs (qualite, tests, tests-integration)

requirements.txt          # Ajout de black, flake8, pytest, pytest-asyncio, httpx (si absents)
database/
└── schema.sql            # Réutilisé tel quel pour peupler le service container Postgres en CI
```

**Structure Decision**: Un seul fichier de workflow `ci.yml` à la racine de `.github/workflows/`
(convention GitHub standard). Aucune nouvelle arborescence de code applicatif — cette feature
est purement de la configuration d'infrastructure CI, cohérente avec la mention
"CI/CD: GitHub Actions" du tech stack de la constitution (S7).

## Détail des 3 jobs du workflow

### Job 1 — `qualite` (Black + Flake8)

| Étape | Action |
| ----- | ------ |
| 1 | `actions/checkout@v4` — récupère le code |
| 2 | `actions/setup-python@v5` — installe Python 3.11 avec cache pip |
| 3 | `pip install -r requirements.txt` |
| 4 | `black --check .` — échoue si code non formaté (ne reformate pas, contrairement au hook local) |
| 5 | `flake8 --max-line-length=88` — échoue si erreurs de lint |

### Job 2 — `tests` (unitaires + contrats, sans DB)

| Étape | Action |
| ----- | ------ |
| 1-3 | identique au Job 1 (checkout, setup Python, install deps) |
| 4 | `pytest -m "not integration" -v` — exécute `tests/unit/` et `tests/contract/` |

Aucun service externe requis — ces tests utilisent SQLite in-memory ou des mocks
(cf. `tests/unit/test_crud.py`, déjà conçu "pour tourner en CI sans base de données réelle").

### Job 3 — `tests-integration` (avec service PostgreSQL)

| Étape | Action |
| ----- | ------ |
| 1 | Déclaration d'un `services: postgres:` (image `postgres:15-alpine`, env `POSTGRES_USER/PASSWORD/DB`, port `5432:5432`, `options: --health-cmd pg_isready`) |
| 2-4 | checkout, setup Python, install deps |
| 5 | Charger le schéma (régions incluses via les `INSERT` déjà présents dans le DDL) : `psql -h localhost -U assuml_user -d assuml_db -f database/schema.sql` |
| 6 | Définir les variables d'environnement attendues par `database/connection.py` (`DB_HOST=localhost`, `DB_USER`, `DB_PASS`, `DB_NAME`, `DB_PORT=5432`) |
| 7 | `pytest -m integration -v` — exécute `tests/integration/` |

## Déclencheurs et optimisations

- **`on.push`**: toutes branches — retour rapide pendant le développement.
- **`on.pull_request`**: vers `main` — affiche le statut comme "check" sur la PR (US4).
- **`concurrency`**: groupe par branche (`group: ci-${{ github.ref }}`, `cancel-in-progress: true`) — annule les exécutions obsolètes lors de pushs successifs rapprochés (FR-010).
- **Cache pip**: via `actions/setup-python@v5` (`cache: 'pip'`) — réduit le temps d'installation des dépendances (FR-009).

## Phases suivantes

- **Phase 0 (research.md)**: documenter les décisions (image Postgres, méthode de seed, gestion des credentials de test, stratégie de cache).
- **Phase 1**: rédiger `ci.yml` complet selon la structure ci-dessus.
- **Phase 2 (tasks.md)**: découper en tâches exécutables via `/speckit-tasks` avant implémentation.

**Hors-scope** (cf. spec.md "Hors-scope") : build/publication Docker (CD), branch protection rules, déploiement.
