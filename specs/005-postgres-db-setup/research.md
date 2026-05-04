# Research: Base de Données PostgreSQL — Schéma & Couche d'Accès

**Feature**: `005-postgres-db-setup` | **Date**: 2026-05-04

---

## Décision 1 — Réutilisation partielle des transformations existantes

**Décision** : `load_csv.py` utilise `rename_columns()` de `cleaning.py` pour les renommages
de colonnes, mais N'utilise PAS `encode_categoricals()` de `normalization.py`.

**Rationale** : `encode_categoricals()` encode pour le ML (sexe→0/1, fumeur→0/1, region→one-hot).
La base de données stocke des valeurs métier lisibles (`sexe VARCHAR CHECK homme/femme`,
`fumeur BOOLEAN`, `region_id INTEGER FK`). Le mapping pour la BDD est différent :
- `sexe` : male→'homme', female→'femme' (string, pas entier)
- `fumeur` : yes→True, no→False (boolean Python)
- `region` : string → `region_id` via SELECT sur `regions` (pas de one-hot)

Le chargement CSV requiert ses propres transformations, distinctes du pipeline ML.

**Alternatives considérées** :
- Tout réutiliser de normalization.py → rejeté (encodage ML incompatible avec le schéma BDD)
- Dupliquer rename_columns() → rejeté (DRY — la fonction existe déjà dans cleaning.py)

---

## Décision 2 — Pattern SQLAlchemy 2.0 avec sessionmaker

**Décision** : `database/connection.py` expose `engine`, `SessionLocal = sessionmaker(...)`, et
`get_db()` generator (dépendance FastAPI). Pas d'utilisation de `async` pour cette feature.

```python
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Rationale** : SQLAlchemy 2.0 sync est suffisant pour 1338 lignes et les besoins actuels de l'API.
L'async (avec `asyncpg`) serait nécessaire si l'API devait gérer des milliers de requêtes simultanées —
hors scope pour une certification. Le pattern `get_db()` generator est la convention FastAPI officielle
et permet le test unitaire par injection de dépendance.

**Alternatives considérées** :
- SQLAlchemy async + asyncpg : trop complexe pour le scope actuel — rejeté
- Connexion directe psycopg2 : pas d'ORM, CRUD verbose — rejeté

---

## Décision 3 — Modèles ORM avec DeclarativeBase SQLAlchemy 2.0

**Décision** : `database/models.py` utilise `DeclarativeBase` (style SQLAlchemy 2.0), une classe
par table, avec les types `Mapped` et `mapped_column`.

```python
class Base(DeclarativeBase):
    pass

class Region(Base):
    __tablename__ = "regions"
    region_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom_region: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
```

**Rationale** : SQLAlchemy 2.0 `DeclarativeBase` est la syntaxe courante (vs `declarative_base()`
deprecated en 2.0). Les annotations `Mapped[T]` apportent la vérification de type statique.
Les contraintes CHECK du schema.sql sont dupliquées dans les modèles ORM via `CheckConstraint`
pour la cohérence.

**Alternatives considérées** :
- SQLAlchemy 1.4 style (`declarative_base()`) : deprecated — rejeté
- Pydantic seul sans ORM : pas de gestion de session, pas d'ORM — rejeté

---

## Décision 4 — Chargement CSV idempotent via TRUNCATE + INSERT

**Décision** : `database/load_csv.py` effectue `TRUNCATE TABLE clients RESTART IDENTITY CASCADE`
avant chaque INSERT. Le résultat est toujours 1338 lignes après exécution.

**Rationale** : Un double-chargement sans TRUNCATE créerait des doublons sans contrainte d'unicité
sur les colonnes métier de `clients`. TRUNCATE est atomique sous PostgreSQL et remet les séquences
à zéro (`RESTART IDENTITY`). CASCADE propage le TRUNCATE aux tables filles (predictions, contrats)
pour éviter les violations FK — acceptable en environnement de développement/démo.

**Alternatives considérées** :
- INSERT ... ON CONFLICT DO NOTHING : pas de clé naturelle sur clients (pas d'email obligatoire) — rejeté
- Vérifier si la table est vide avant d'insérer : non idempotent — rejeté

---

## Décision 5 — Script de test `scripts/setup_db.py`

**Décision** : Script Python standalone qui orchestre en séquence :
1. Teste la connexion PostgreSQL
2. Exécute `database/schema.sql` via `psycopg2` (pas SQLAlchemy pour le DDL)
3. Lance `database/load_csv.py` (chargement 1338 lignes)
4. Affiche un rapport de validation (COUNT par table, exemples de données)

**Rationale** : Un script unique d'initialisation réduit les étapes manuelles à une seule commande.
Le DDL (`schema.sql`) est exécuté via `psycopg2` brut pour garantir le respect exact du fichier SQL
sans traduction ORM. Le chargement utilise la couche `load_csv.py` pour la réutilisabilité.

**Alternatives considérées** :
- Alembic pour les migrations : trop complexe pour l'initialisation initiale — différé à la feature API
- `Base.metadata.create_all(engine)` seul : ne garantit pas la cohérence avec `schema.sql` — rejeté

---

## Décision 6 — Variables d'environnement et DATABASE_URL

**Décision** : `connection.py` charge `.env` via `python-dotenv` et construit `DATABASE_URL` :

```python
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}"
    f"/{os.getenv('DB_NAME')}"
)
```

**Variables requises** : `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS`.
Un `.env.example` commité documente ces 5 variables sans valeurs réelles.

**Rationale** : Pattern standard `12-factor app`. `python-dotenv` est déjà dans les dépendances
du projet. Les valeurs par défaut (`localhost`, `5432`) évitent les erreurs si `.env` est partiel.

**Alternatives considérées** :
- Variables d'environnement shell sans `.env` : moins pratique en développement local — rejeté
- Fichier de config YAML : surcharge inutile pour 5 variables — rejeté

---

## Décision 7 — Index partiel sur clients actifs

**Décision** :

```sql
CREATE INDEX idx_clients_actifs ON clients (client_id)
WHERE date_suppression IS NULL;
```

**Rationale** : L'index partiel couvre uniquement les clients non supprimés — la grande majorité
des requêtes de l'API filtre sur `date_suppression IS NULL` (get_clients, souscription, scoring).
Un index total inclurait les clients supprimés logiquement qui ne sont jamais relus.

**Alternatives considérées** :
- Index total sur `date_suppression` : moins sélectif, moins efficace — rejeté
- Pas d'index sur `date_suppression` : requêtes lentes sur grande volumétrie — rejeté

---

## Aucun NEEDS CLARIFICATION

Tous les choix techniques ont été résolus par les arguments explicites de `/speckit-plan`
et par la constitution AssuML (Principes III et IV).
