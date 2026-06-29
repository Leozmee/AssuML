# Quickstart: Seed Database

**Feature**: 011-seed-database | **Date**: 2026-06-13

## Lancer le seed en local (sans Docker)

```bash
# Prérequis : PostgreSQL en cours d'exécution + .env configuré
# S'assurer que le schéma est chargé
psql -h localhost -U assuml_user -d assuml_db -f database/schema.sql

# Lancer le seed
python database/seed.py
# → "4 régions insérées, 1 338 clients insérés"

# Relancer (idempotent)
python database/seed.py
# → "Base déjà peuplée, seed ignoré"
```

## Lancer via Docker Compose

```bash
# Premier démarrage — construit les images et peuple la base
docker compose up --build

# Les services démarrent dans cet ordre :
# 1. postgres (healthcheck pg_isready)
# 2. seed     (python database/seed.py → se termine)
# 3. api      (uvicorn port 8000)
# 4. streamlit (streamlit run port 8501)

# Vérifier le seed
docker compose logs seed
# → "4 régions insérées, 1 338 clients insérés"

# Accès app
# API  : http://localhost:8000/docs
# App  : http://localhost:8501
```

## Variables d'environnement requises

```bash
# .env (local) ou docker-compose environment (Docker)
DB_HOST=localhost      # ou "postgres" dans Docker
DB_PORT=5432
DB_USER=assuml_user
DB_PASS=<mot_de_passe>
DB_NAME=assuml_db
```

## Vérifier la base après seed

```bash
psql -h localhost -U assuml_user -d assuml_db -c \
  "SELECT COUNT(*) FROM clients; SELECT COUNT(*) FROM predictions;"
# clients: 1338 | predictions: 0
```

## Tests

```bash
# Tests unitaires (transformations — sans BDD)
pytest tests/unit/test_seed_transforms.py -v

# Tests d'intégration (nécessite PostgreSQL)
pytest tests/integration/test_seed_database.py -v -m integration
```

## Structure des fichiers livrés

```text
database/seed.py                          ← script principal
docker-compose.yml                        ← orchestration complète
Dockerfile                                ← image Python multi-usage
tests/unit/test_seed_transforms.py        ← tests transformations
tests/integration/test_seed_database.py  ← tests comptage lignes
```
