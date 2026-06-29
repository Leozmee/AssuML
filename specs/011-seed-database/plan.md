# Implementation Plan: Seed Database — Clients initiaux

**Branch**: `011-seed-database` | **Date**: 2026-06-13 | **Spec**: [spec.md](spec.md)

## Summary

Créer `database/seed.py` pour peupler automatiquement PostgreSQL avec les 4 régions et les 1 338 clients de `insurance.csv` au démarrage Docker. Le script est idempotent, standalone, et laisse `predictions`/`contrats`/`sinistres` vides pour que le flux métier scoring reste intact. Intégré via un service `seed` dans `docker-compose.yml`.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: SQLAlchemy 2.0+ (ORM existant), Pandas 2.0+, python-dotenv
**Storage**: PostgreSQL 15+ — tables `regions` et `clients` uniquement
**Testing**: pytest — 1 test unitaire (transformations) + 1 test d'intégration (comptage lignes)
**Target Platform**: Linux (container Docker) + macOS (dev local)
**Project Type**: Script standalone + service Docker Compose
**Performance Goals**: 1 338 lignes insérées en < 30 secondes
**Constraints**: Idempotent (0 doublon si relancé), exit code 1 si CSV absent ou BDD inaccessible
**Scale/Scope**: 1 338 clients, 4 régions, batch de 500 lignes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Statut | Justification |
|----------|--------|---------------|
| **I — Trois sources** | ✅ | `seed.py` utilise `insurance.csv` (source CSV obligatoire). Les deux autres sources (API météo, scraping articles) sont hors scope de cette feature et déjà implémentées. |
| **II — ML rigoureux** | ✅ | `seed.py` n'insère PAS dans `predictions`. Les modèles ML ne sont pas sollicités ici. Le flux scoring reste déclenché uniquement par l'assureur via Streamlit. |
| **III — Séparation des couches** | ✅ | `seed.py` est un script de démarrage, pas un endpoint API. Il accède à PostgreSQL directement via SQLAlchemy (légitimement — c'est un outil d'administration, pas Streamlit). |
| **IV — RGPD & sécurité** | ✅ | `email` et `telephone` restent NULL (RGPD). Connexion via variables d'env (pas de credentials hardcodés). Pas de soft delete requis ici (insertion initiale). |
| **V — Qualité & tests** | ✅ | `seed.py` aura docstrings françaises, commentaires français, couverture pytest (unit + intégration), PEP8 flake8+black. |

## Project Structure

### Documentation (this feature)

```text
specs/011-seed-database/
├── plan.md              ✅ Ce fichier
├── research.md          ✅ Phase 0
├── data-model.md        ✅ Phase 1
├── quickstart.md        ✅ Phase 1
└── tasks.md             (Phase 2 — /speckit-tasks)
```

### Source Code (repository root)

```text
database/
├── seed.py              ← NOUVEAU (script principal)
├── models.py            (existant — ORM Region, Client)
├── connection.py        (existant — engine + SessionLocal)
└── schema.sql           (existant — DDL PostgreSQL)

docker-compose.yml       ← NOUVEAU (à créer — service seed + postgres + api + streamlit)

tests/
├── unit/
│   └── test_seed_transforms.py     ← NOUVEAU
└── integration/
    └── test_seed_database.py       ← NOUVEAU
```

## Phase 0: Research

*Voir [research.md](research.md)*

## Phase 1: Design

*Voir [data-model.md](data-model.md) et [quickstart.md](quickstart.md)*
