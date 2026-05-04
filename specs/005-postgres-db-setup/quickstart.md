# Quickstart: Base de Données PostgreSQL

**Feature**: `005-postgres-db-setup` | **Date**: 2026-05-04

---

## Prérequis

```bash
# 1. PostgreSQL 15+ installé
brew install postgresql@15
brew services start postgresql@15

# 2. Créer l'utilisateur et la base
psql postgres -c "CREATE USER assuml_user WITH PASSWORD 'assuml_pass';"
psql postgres -c "CREATE DATABASE assuml_db OWNER assuml_user;"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE assuml_db TO assuml_user;"

# 3. Vérifier le .env (copier depuis .env.example)
cp .env.example .env
# Éditer .env si les valeurs par défaut ne conviennent pas

# 4. Vérifier les dépendances Python
python -c "import sqlalchemy, psycopg2, dotenv; print('OK')"
```

---

## Initialisation complète en une commande

```bash
python scripts/setup_db.py

# Sortie attendue :
# ✅ Connexion PostgreSQL OK (assuml_db @ localhost:5432)
# ✅ Schéma créé : 7 tables, 22 contraintes, 21 index
# ✅ Données chargées : 1338 clients
# --- Rapport de validation ---
# regions      : 4 lignes
# clients      : 1338 lignes (1338 actifs, 0 supprimés)
# predictions  : 0 lignes
# contrats     : 0 lignes
# sinistres    : 0 lignes
# donnees_meteo: 0 lignes
# articles     : 0 lignes
```

---

## Étapes séparées

```bash
# Schéma uniquement
psql -U assuml_user -d assuml_db -f database/schema.sql

# Chargement CSV uniquement (après schema)
python database/load_csv.py

# Vérification connexion Python
python -c "
from database.connection import engine
with engine.connect() as conn:
    result = conn.execute('SELECT COUNT(*) FROM clients')
    print('Clients:', result.scalar())
"
```

---

## Utilisation de la couche CRUD

```python
from database.connection import SessionLocal
from database import crud

db = SessionLocal()

# Créer un client
from database.models import Client
client = crud.create_client(db, age=35, sexe='homme', imc=24.5,
                             enfants=2, fumeur=False, region_id=1)
print(f"Client créé : id={client.client_id}")

# Lister les clients actifs
clients = crud.get_clients(db, actifs_only=True)
print(f"Clients actifs : {len(clients)}")

# Soft delete
crud.soft_delete_client(db, client.client_id)
print(f"Client {client.client_id} supprimé logiquement")

# Créer une prédiction
pred = crud.create_prediction(db,
    client_id=client.client_id,
    cout_predit=15000.0,
    score_risque=0.87,
    categorie_risque='eleve',
    decision='examiner',
    prime=20250.0,
    version_modele='1.1.0'
)
print(f"Prédiction créée : id={pred.prediction_id}")

db.close()
```

---

## Vérification du schéma

```bash
# Lister les tables
psql -U assuml_user -d assuml_db -c "\dt"

# Vérifier les contraintes CHECK
psql -U assuml_user -d assuml_db -c "
SELECT conname, contype, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid IN (SELECT oid FROM pg_class WHERE relname IN
    ('clients','predictions','contrats','sinistres','donnees_meteo','regions'))
ORDER BY conrelid, contype;
"

# Tester une violation CHECK
psql -U assuml_user -d assuml_db -c "
INSERT INTO clients (region_id, age, sexe, imc, enfants, fumeur)
VALUES (1, 15, 'homme', 22.0, 0, FALSE);
"
# → ERROR: new row violates check constraint "clients_age_check"

# Tester soft delete
psql -U assuml_user -d assuml_db -c "
SELECT client_id, date_suppression FROM clients
WHERE date_suppression IS NOT NULL LIMIT 5;
"
```

---

## Fichiers produits

| Fichier | Commité | Description |
|---------|---------|-------------|
| `database/schema.sql` | ✅ | DDL complet — 7 tables, 22 CHECK, 21 index |
| `database/connection.py` | ✅ | engine, SessionLocal, get_db() |
| `database/models.py` | ✅ | 7 modèles ORM SQLAlchemy 2.0 |
| `database/crud.py` | ✅ | 9 fonctions CRUD |
| `database/load_csv.py` | ✅ | Chargement 1338 lignes CSV |
| `database/__init__.py` | ✅ | Module Python |
| `scripts/setup_db.py` | ✅ | Script d'initialisation complet |
| `.env.example` | ✅ | Variables d'environnement documentées |
| `.env` | ❌ | Credentials réels (gitignored) |
