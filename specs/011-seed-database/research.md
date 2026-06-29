# Research: Seed Database

**Feature**: 011-seed-database | **Date**: 2026-06-13

## Décision 1 — Stratégie d'insertion batch

**Decision**: `session.bulk_insert_mappings(Client, records)` en chunks de 500 lignes.

**Rationale**: `bulk_insert_mappings` contourne le tracking ORM (pas d'objet Python instancié par ligne) et génère un seul INSERT multi-values par chunk → ordre de grandeur 10× plus rapide qu'`add_all()` sur 1 338 lignes. Les chunks de 500 évitent les timeouts réseau et les limites de paramètres PostgreSQL (max ~32 000 paramètres par requête).

**Alternatives considérées**:
- `session.add_all()` : plus lisible mais instancie 1 338 objets ORM — inutile pour un seed.
- `engine.execute()` avec SQL brut : plus rapide encore mais perd la cohérence avec les modèles ORM existants et les contraintes CHECK.
- `pandas.DataFrame.to_sql()` : simple mais ne respecte pas les FK et bypasse les contraintes ORM.

---

## Décision 2 — Gestion de la connexion BDD

**Decision**: Réutiliser `database/connection.py` tel quel (engine + SessionLocal). Lire `DATABASE_URL` depuis les variables d'environnement via `python-dotenv`.

**Rationale**: `connection.py` utilise déjà `os.getenv()` pour construire l'URL. Dans le container Docker, les variables sont injectées par `docker-compose.yml`. En local, elles viennent du `.env`. Aucune modification de `connection.py` nécessaire.

**Point d'attention**: `connection.py` construit l'URL depuis 5 variables séparées (`DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT`, `DB_NAME`). Le `docker-compose.yml` doit injecter ces 5 variables (et non `DATABASE_URL` comme mentionné dans les contraintes) pour rester cohérent avec le code existant.

---

## Décision 3 — Idempotence

**Decision**: `SELECT COUNT(*) FROM clients` avant toute insertion. Si > 0 → log + exit 0 (pas d'erreur, juste ignoré).

**Rationale**: Pattern le plus simple et le plus lisible. Pas besoin d'upsert (`INSERT ... ON CONFLICT`) car le seed est une opération one-shot. Si la table est vide mais les régions existent déjà, on insère quand même les clients (cas: relance après crash partiel).

**Alternatives considérées**:
- `INSERT ... ON CONFLICT DO NOTHING` : fonctionne mais masque les erreurs de données.
- Vérifier un fichier `.seed_done` : fragile en Docker (fichier perdu entre runs).

---

## Décision 4 — Lookup region → region_id

**Decision**: Charger les 4 régions en mémoire au début du script sous forme de dict `{nom_region: region_id}`, puis mapper chaque ligne CSV.

**Rationale**: 4 régions uniquement → dict en mémoire trivial. Un seul SELECT au démarrage au lieu d'une requête par ligne CSV.

```python
regions_map = {r.nom_region: r.region_id for r in session.query(Region).all()}
# → {'southwest': 1, 'southeast': 2, 'northwest': 3, 'northeast': 4}
```

---

## Décision 5 — docker-compose.yml

**Decision**: Créer `docker-compose.yml` à la racine avec 4 services : `postgres`, `seed`, `api`, `streamlit`.

**Rationale**: `docker-compose.yml` n'existe pas encore dans le projet. Cette feature est l'occasion naturelle de le créer. Le service `seed` dépend de `postgres` (condition: `service_healthy`). Les services `api` et `streamlit` dépendent de `seed` (condition: `service_completed_successfully`) pour garantir que la base est peuplée avant que l'app démarre.

**Structure Docker**:
- `postgres` : image officielle `postgres:15-alpine`, healthcheck `pg_isready`
- `seed` : `build: .` avec `command: python database/seed.py`, `restart: on-failure`
- `api` : `build: .` avec `command: uvicorn api.main:app`, dépend de `seed`
- `streamlit` : `build: .` avec `command: streamlit run streamlit_app/app.py`, dépend de `api`

---

## Décision 6 — Dockerfile

**Decision**: Créer un `Dockerfile` multi-usage (utilisé par `seed`, `api` et `streamlit`).

**Rationale**: Image unique basée sur `python:3.11-slim`, `COPY requirements.txt` + `pip install`, puis `COPY . .`. Chaque service surcharge la `command` dans `docker-compose.yml`. Évite de maintenir 3 Dockerfiles distincts pour la même stack Python.
