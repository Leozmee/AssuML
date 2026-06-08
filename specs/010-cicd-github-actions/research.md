# Research: CI/CD — GitHub Actions (Black, Flake8, Pytest)

**Feature**: 010-cicd-github-actions
**Date**: 2026-06-08
**Status**: Complet — toutes les décisions résolues

## Décisions techniques

### 1. Plateforme et image de base

**Decision**: GitHub Actions, runner `ubuntu-latest`, Python 3.11 (`actions/setup-python@v5`).

**Rationale**: Le repo est déjà hébergé sur GitHub (cf. constitution : "Versioning : Git + GitHub" et "CI/CD : GitHub Actions + Docker") ; aucun coût d'intégration supplémentaire. `ubuntu-latest` est le runner standard, gratuit pour les repos publics/éducatifs, et compatible avec tous les outils du projet (Black, Flake8, Pytest, psql).

**Alternatives considérées**: GitLab CI, CircleCI — écartés car le repo est sur GitHub et la constitution mentionne explicitement GitHub Actions.

---

### 2. Découpage en jobs séparés vs un seul job séquentiel

**Decision**: 3 jobs indépendants — `qualite`, `tests`, `tests-integration` — exécutés en parallèle (pas de `needs:` entre eux).

**Rationale**: Un job qui échoue rapidement (Black/Flake8, < 2 min) donne un retour immédiat sans attendre la fin des tests d'intégration (le plus lent, à cause du démarrage du conteneur PostgreSQL). L'exécution en parallèle (plutôt qu'en séquence avec `needs:`) minimise le temps total d'attente : un développeur voit en quelques minutes l'ensemble des résultats plutôt que d'attendre la fin du job précédent pour démarrer le suivant.

**Alternatives considérées**: Un seul job séquentiel (Black → Flake8 → Pytest unit → Pytest integration), comme le hook local — écarté car cela rallonge le temps total de feedback (chaque étape attend la précédente) sans bénéfice : en CI, contrairement au hook local, il n'y a pas de "fail fast" nécessaire pour économiser le temps du développeur (les jobs tournent sur les serveurs GitHub, pas sur sa machine).

---

### 3. Service container PostgreSQL pour les tests d'intégration

**Decision**: Déclarer un service `postgres:15-alpine` dans le job `tests-integration` via la clé `services:` de GitHub Actions, avec :
```yaml
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_USER: assuml_user
      POSTGRES_PASSWORD: ${{ secrets.CI_DB_PASSWORD }}   # valeur de test, jamais la vraie
      POSTGRES_DB: assuml_db
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

**Rationale**: GitHub Actions gère nativement le cycle de vie du conteneur (démarrage, healthcheck, arrêt) sans configuration Docker Compose supplémentaire. L'option `--health-cmd pg_isready` garantit que le job attend que PostgreSQL soit réellement prêt à accepter des connexions avant de lancer les étapes suivantes — élimine les faux échecs dus à un démarrage trop lent.

**Alternatives considérées**: `docker-compose up` dans le job — plus complexe à orchestrer (réseau, volumes, attente manuelle) pour un seul service ; les "service containers" natifs sont l'approche recommandée par GitHub pour ce cas exact.

---

### 4. Chargement du schéma et des données de seed

**Decision**: Charger uniquement `database/schema.sql` via `psql` en ligne de commande
(`psql -h localhost -U assuml_user -d assuml_db -f database/schema.sql`). Aucun script de
seed séparé n'est nécessaire : le DDL contient déjà les `INSERT INTO regions (nom_region)
VALUES (...)` (lignes 28+) qui peuplent la table de référence avec les 4 régions
(`southwest`, `southeast`, `northwest`, `northeast`) attendues par
`tests/integration/test_db_connection.py::test_regions_preremplies`.

**Rationale**: Réutilise le DDL déjà versionné (`database/schema.sql`, idempotent —
`DROP TABLE IF EXISTS ... CASCADE` en tête) — source de vérité unique, pas de duplication
de schéma/seed entre local et CI. Une seule commande suffit à amener la base dans l'état
exact attendu par les tests d'intégration.

**Alternatives considérées**: Recréer le schéma via SQLAlchemy `Base.metadata.create_all()` — écarté car cela ne testerait pas le DDL réel (`schema.sql`) utilisé en production, et pourrait masquer des désynchronisations entre le DDL versionné et les modèles ORM.

---

### 5. Gestion des credentials de test

**Decision**: Stocker le mot de passe PostgreSQL utilisé en CI comme **secret GitHub** (`secrets.CI_DB_PASSWORD`), distinct des vraies credentials `.env` (jamais commitées, cf. `.gitignore`). Les variables `DB_HOST`, `DB_USER`, `DB_NAME`, `DB_PORT` sont définies directement dans le workflow (valeurs non sensibles, propres à l'environnement CI éphémère).

**Rationale**: Respecte le principe constitutionnel "Jamais de credentials hardcodés — utiliser `.env`" (Principe IV, RGPD/sécurité) : même en CI, aucun secret n'apparaît en clair dans le YAML versionné. Le conteneur PostgreSQL de CI est éphémère (détruit en fin de job) et totalement isolé de la base de production.

**Alternatives considérées**: Hardcoder un mot de passe "de test" directement dans le YAML — techniquement sans risque réel (conteneur jetable, réseau isolé) mais déconseillé car cela créerait une habitude contraire à la règle du projet et pourrait être copié-collé dans un contexte sensible par erreur.

---

### 6. Cache des dépendances et annulation des runs obsolètes

**Decision**:

- Cache pip natif via `actions/setup-python@v5` avec `cache: 'pip'` (clé basée sur le hash de `requirements.txt`).
- `concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }` au niveau du workflow.

**Rationale**: Le cache pip évite de retélécharger ~25 dépendances (pandas, scikit-learn, fastapi, duckdb, etc., certaines volumineuses) à chaque run — gain de plusieurs dizaines de secondes par job. La concurrency annule automatiquement les exécutions devenues obsolètes (ex: 3 pushs rapprochés sur la même branche ne lancent pas 3 pipelines complets en parallèle), économisant les minutes CI (ressource limitée même sur les comptes éducatifs).

**Alternatives considérées**: Pas de cache (run plus lent, mais plus simple) — écarté car le gain de temps est significatif pour un projet avec autant de dépendances ML/data lourdes.

---

### 7. Déclencheurs (triggers)

**Decision**:

```yaml
on:
  push:
  pull_request:
    branches: [main]
```

**Rationale**: `push` sans filtre de branche donne un retour à chaque branche de travail (comportement proche du hook pre-commit local, mais après coup). `pull_request` ciblé sur `main` affiche les checks sur les PR de fusion (US4) sans dupliquer l'exécution (GitHub évite par défaut de relancer le même commit deux fois grâce à la déduplication push/PR sur la même réf).

**Alternatives considérées**: Limiter `push` à certaines branches (`main`, `develop`) — écarté car cela retarderait la détection des problèmes jusqu'à l'ouverture d'une PR, alors que l'objectif est un retour aussi rapide que le hook local.

---

### 8. CD (build/déploiement Docker) — explicitement reporté

**Decision**: Ne pas inclure de job de build/publication d'image Docker dans cette feature.

**Rationale**: Aucun `Dockerfile`/`docker-compose.yml` n'existe encore dans le repo (vérifié — absent de la racine). La constitution mentionne Docker dans le tech stack CI/CD (S7), mais construire un pipeline CD sans artefact Docker à produire serait prématuré et hors du périmètre testable de cette spec. Cette partie fera l'objet d'une feature dédiée une fois les Dockerfiles écrits.

**Alternatives considérées**: Inclure un job "build" vide en placeholder — écarté pour éviter le faux sentiment qu'une étape fonctionne alors qu'elle ne fait rien d'utile (anti-pattern : job qui "passe" sans valeur).
