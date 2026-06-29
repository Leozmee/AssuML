# Tasks: Seed Database — Clients initiaux

**Input**: Design documents from `specs/011-seed-database/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]** : peut tourner en parallèle (fichiers différents, pas de dépendance)
- **[Story]** : user story concernée (US1, US2, US3)
- Chemins exacts dans les descriptions

---

## Phase 1 : Setup (Infrastructure partagée)

**Objectif** : Créer les fichiers de base nécessaires au script et à l'orchestration Docker.

- [X] T001 Créer `Dockerfile` à la racine (image `python:3.11-slim`, `COPY requirements.txt`, `pip install`, `COPY . .`)
- [X] T002 [P] Créer `docker-compose.yml` à la racine avec le service `postgres` (image `postgres:15-alpine`, healthcheck `pg_isready`, variables DB_*)

**Checkpoint** : `docker compose up postgres` démarre PostgreSQL et passe le healthcheck.

---

## Phase 2 : Fondation (Prérequis bloquants)

**Objectif** : Créer le squelette de `database/seed.py` avec la connexion BDD et la structure du module.

**⚠️ CRITIQUE** : Aucune fonction de seed ne peut être implémentée avant cette phase.

- [X] T003 Créer `database/seed.py` : imports (`logging`, `sys`, `pandas`, `sqlalchemy`), configuration du logger (`logging.basicConfig`), constante `CHEMIN_CSV = Path("data/small_data/insurance.csv")`, import de `SessionLocal` et des modèles `Region`, `Client` depuis `database/connection.py` et `database/models.py`
- [X] T004 [P] Créer `tests/unit/test_seed_transforms.py` : fichier vide avec imports (`pytest`) et marqueur de module si nécessaire
- [X] T005 [P] Créer `tests/integration/test_seed_database.py` : fichier vide avec `import pytest` et `pytestmark = pytest.mark.integration`

**Checkpoint** : `python database/seed.py` s'exécute sans erreur d'import (même si le script ne fait rien encore).

---

## Phase 3 : User Story 1 — Démarrage Docker avec base peuplée (Priority: P1) 🎯 MVP

**Objectif** : Le service seed peuple `regions` et `clients` au `docker compose up`.

**Test indépendant** : `docker compose up` → `GET /api/clients/` retourne 1 338 entrées.

### Tests pour US1

- [X] T006 [US1] Implémenter dans `tests/unit/test_seed_transforms.py` : `test_mapping_sexe_male()`, `test_mapping_sexe_female()`, `test_mapping_fumeur_yes()`, `test_mapping_fumeur_no()`, `test_regions_definies()` — tester les fonctions de transformation pures (sans BDD)
- [X] T007 [US1] Implémenter dans `tests/integration/test_seed_database.py` : `test_regions_count()` (4 lignes), `test_clients_count()` (1 338 lignes), `test_seed_idempotent()` (relancer → même count) — utiliser une session SQLAlchemy sur la BDD de test

### Implémentation US1

- [X] T008 [US1] Implémenter `transformer_ligne(row, regions_map)` dans `database/seed.py` : convertit une ligne du CSV en dict `{region_id, age, sexe, imc, enfants, fumeur}` avec les mappings `sex→sexe`, `bmi→imc`, `children→enfants`, `smoker→fumeur`, `region→region_id`
- [X] T009 [US1] Implémenter `seed_regions(session)` dans `database/seed.py` : `SELECT COUNT(*) FROM regions`, si 0 alors `session.bulk_insert_mappings(Region, [...4 régions...])`, logger le résultat
- [X] T010 [US1] Implémenter `seed_clients(session)` dans `database/seed.py` : lire CSV avec `pandas.read_csv()`, charger `regions_map`, vérifier `COUNT(*) FROM clients`, si 0 alors transformer chaque ligne et `bulk_insert_mappings` par chunks de 500, logger le résultat
- [X] T011 [US1] Implémenter `main()` dans `database/seed.py` : `SessionLocal()`, appeler `seed_regions()` puis `seed_clients()`, `session.commit()`, gérer `FileNotFoundError` (CSV absent → log + `sys.exit(1)`), gérer `OperationalError` (BDD inaccessible → log + `sys.exit(1)`), bloc `if __name__ == "__main__": main()`
- [X] T012 [US1] Ajouter le service `seed` dans `docker-compose.yml` : `build: .`, `command: python database/seed.py`, `depends_on: postgres: condition: service_healthy`, `restart: "on-failure"`, variables d'env `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, `DB_NAME`

**Checkpoint** : `python database/seed.py` en local → "4 régions insérées, 1 338 clients insérés". Relancer → "Base déjà peuplée, seed ignoré".

---

## Phase 4 : User Story 2 — Données lisibles et métier (Priority: P2)

**Objectif** : Vérifier que les transformations produisent des valeurs françaises correctes en base.

**Test indépendant** : `GET /api/clients/1` → `sexe="homme"`, `fumeur=false`, `region_id` valide.

### Tests pour US2

- [X] T013 [US2] Ajouter dans `tests/unit/test_seed_transforms.py` : `test_imc_arrondi()` (bmi=27.900 → imc=Decimal('27.90')), `test_region_lookup_valide()` (region='southwest' → region_id=1), `test_region_inconnue_leve_erreur()` (region='unknown' → KeyError ou ValueError)

### Implémentation US2

- [X] T014 [US2] Mettre à jour `transformer_ligne()` dans `database/seed.py` : ajouter arrondi `imc` à 2 décimales (`round(float(row['bmi']), 2)`), lever `ValueError` explicite si `region` absente du `regions_map`, cast `age` et `enfants` en `int`

**Checkpoint** : `pytest tests/unit/test_seed_transforms.py -v` → tous les tests passent.

---

## Phase 5 : User Story 3 — Table predictions vide au démarrage (Priority: P3)

**Objectif** : Garantir que `seed.py` ne touche jamais `predictions`, `contrats`, `sinistres`.

**Test indépendant** : Après seed, `SELECT COUNT(*) FROM predictions` = 0.

### Tests pour US3

- [X] T015 [US3] Ajouter dans `tests/integration/test_seed_database.py` : `test_predictions_vide()`, `test_contrats_vide()`, `test_sinistres_vide()` — vérifier que les 3 tables métier sont vides après seed

**Checkpoint** : `pytest tests/integration/test_seed_database.py -v -m integration` → tous les tests passent.

---

## Phase 6 : Polish & Finalisation

**Objectif** : Intégration Docker complète, qualité code, services `api` et `streamlit`.

- [X] T016 [P] Ajouter les services `api` et `streamlit` dans `docker-compose.yml` : `api` (`command: uvicorn api.main:app --host 0.0.0.0 --port 8000`, `depends_on: seed: condition: service_completed_successfully`, port `8000:8000`), `streamlit` (`command: streamlit run streamlit_app/app.py --server.port 8501`, `depends_on: api`, port `8501:8501`)
- [X] T017 [P] Vérifier conformité flake8 + black sur `database/seed.py` et les deux fichiers de tests
- [ ] T018 Valider le quickstart complet : `docker compose up --build`, vérifier logs du service seed, vérifier `GET http://localhost:8000/api/clients/` retourne 1 338 entrées, vérifier `GET http://localhost:8000/health` retourne 200

---

## Dépendances & Ordre d'exécution

### Dépendances entre phases

- **Phase 1 (Setup)** : aucune dépendance — démarrer immédiatement
- **Phase 2 (Fondation)** : dépend de Phase 1 — bloque toutes les US
- **Phase 3 (US1)** : dépend de Phase 2 — MVP livrable seul
- **Phase 4 (US2)** : dépend de T008 (transformer_ligne) — peut démarrer en parallèle de T009-T012
- **Phase 5 (US3)** : dépend de Phase 3 complète
- **Phase 6 (Polish)** : dépend de Phase 3 + 4 + 5

### Dépendances internes à US1

```
T008 (transformer_ligne)
    ↓
T009 (seed_regions) ──┐
T010 (seed_clients) ──┤ → T011 (main) → T012 (docker-compose seed)
    ↑                  │
T006 (tests unit) ─────┘
T007 (tests integration)
```

### Opportunités parallèles

- T004 et T005 (squelettes tests) peuvent tourner en parallèle avec T003
- T006 (tests transformations) peut être écrit en parallèle avec T008 (implémentation)
- T013 (tests US2) peut être écrit en parallèle avec T014 (implémentation US2)
- T016 et T017 (Polish) peuvent tourner en parallèle

---

## Stratégie d'implémentation

### MVP (US1 uniquement)

1. Compléter Phase 1 (T001, T002)
2. Compléter Phase 2 (T003, T004, T005)
3. Compléter Phase 3 US1 (T006 → T012)
4. **VALIDER** : `python database/seed.py` → 1 338 clients insérés
5. **VALIDER** : `docker compose up` → seed s'exécute automatiquement

### Livraison complète

1. MVP validé
2. Ajouter US2 (T013, T014) → tests transformations complets
3. Ajouter US3 (T015) → garantie predictions vide
4. Polish (T016, T017, T018) → intégration Docker complète

---

## Notes

- T008 (`transformer_ligne`) doit être une fonction pure testable sans BDD
- L'ordre seed_regions → seed_clients est OBLIGATOIRE (contrainte FK)
- `bulk_insert_mappings` ne déclenche pas les events SQLAlchemy — c'est voulu (performance)
- Le `session.commit()` est dans `main()`, pas dans `seed_regions()`/`seed_clients()` (transaction unique)
- Les tests d'intégration nécessitent PostgreSQL en cours d'exécution
