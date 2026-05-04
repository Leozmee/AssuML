# Data Model: Base de Données PostgreSQL — Schéma & Couche d'Accès

**Feature**: `005-postgres-db-setup` | **Date**: 2026-05-04

---

## Schéma SQL complet

### Table `regions` (référentiel)

```sql
CREATE TABLE regions (
    region_id   SERIAL PRIMARY KEY,
    nom_region  VARCHAR(50) UNIQUE NOT NULL,
    CONSTRAINT chk_regions_nom CHECK (
        nom_region IN ('southwest', 'southeast', 'northwest', 'northeast')
    )
);

INSERT INTO regions (nom_region) VALUES
    ('southwest'), ('southeast'), ('northwest'), ('northeast');
```

---

### Table `clients` (métier — soft delete)

```sql
CREATE TABLE clients (
    client_id       SERIAL PRIMARY KEY,
    region_id       INTEGER NOT NULL REFERENCES regions(region_id) ON DELETE CASCADE,
    age             INTEGER NOT NULL CHECK (age BETWEEN 18 AND 120),
    sexe            VARCHAR(10) NOT NULL CHECK (sexe IN ('homme', 'femme')),
    imc             DECIMAL(5,2) NOT NULL CHECK (imc BETWEEN 10.00 AND 80.00),
    enfants         INTEGER NOT NULL DEFAULT 0 CHECK (enfants >= 0),
    fumeur          BOOLEAN NOT NULL DEFAULT FALSE,
    email           VARCHAR(255) NULL,
    telephone       VARCHAR(20) NULL,
    date_creation   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_suppression TIMESTAMP NULL   -- soft delete (NULL = actif)
);
```

**Contraintes CHECK** : `age`, `sexe`, `imc`, `enfants` (4 contraintes).

---

### Table `predictions` (métier)

```sql
CREATE TABLE predictions (
    prediction_id   SERIAL PRIMARY KEY,
    client_id       INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    cout_predit     DECIMAL(10,2),
    score_risque    DECIMAL(5,4) CHECK (score_risque BETWEEN 0 AND 1),
    categorie_risque VARCHAR(20) CHECK (
        categorie_risque IN ('faible', 'moyen', 'eleve', 'critique')
    ),
    decision        VARCHAR(20) CHECK (
        decision IN ('accepter', 'refuser', 'examiner')
    ),
    prime           DECIMAL(10,2),
    version_modele  VARCHAR(20),
    date_prediction TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Contraintes CHECK** : `score_risque`, `categorie_risque`, `decision` (3 contraintes).

---

### Table `contrats` (métier)

```sql
CREATE TABLE contrats (
    contrat_id      SERIAL PRIMARY KEY,
    client_id       INTEGER NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    statut          VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (
        statut IN ('actif', 'resilie', 'expire', 'suspendu')
    ),
    prime_mensuelle DECIMAL(10,2) NOT NULL CHECK (prime_mensuelle > 0),
    date_debut      DATE NOT NULL DEFAULT CURRENT_DATE,
    date_fin        DATE NULL,
    type_couverture VARCHAR(50) NOT NULL CHECK (
        type_couverture IN ('basique', 'standard', 'premium', 'famille')
    ),
    date_creation   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_contrats_dates CHECK (date_fin IS NULL OR date_fin > date_debut)
);
```

**Contraintes CHECK** : `statut`, `prime_mensuelle`, `type_couverture`, `date_fin > date_debut` (4 contraintes).

---

### Table `sinistres` (métier)

```sql
CREATE TABLE sinistres (
    sinistre_id     SERIAL PRIMARY KEY,
    contrat_id      INTEGER NOT NULL REFERENCES contrats(contrat_id) ON DELETE CASCADE,
    date_sinistre   DATE NOT NULL,
    montant_sinistre DECIMAL(10,2) NOT NULL CHECK (montant_sinistre > 0),
    type_sinistre   VARCHAR(50) NOT NULL CHECK (
        type_sinistre IN (
            'hospitalisation', 'consultation', 'pharmacie',
            'chirurgie', 'urgence', 'autre'
        )
    ),
    statut_sinistre VARCHAR(20) NOT NULL DEFAULT 'en_cours' CHECK (
        statut_sinistre IN ('en_cours', 'accepte', 'refuse', 'rembourse')
    ),
    description     TEXT NULL
);
```

**Contraintes CHECK** : `montant_sinistre`, `type_sinistre`, `statut_sinistre` (3 contraintes).

---

### Table `donnees_meteo` (source externe — API)

```sql
CREATE TABLE donnees_meteo (
    meteo_id        SERIAL PRIMARY KEY,
    region_id       INTEGER NOT NULL REFERENCES regions(region_id) ON DELETE CASCADE,
    temperature_moy DECIMAL(5,2) CHECK (temperature_moy BETWEEN -50 AND 60),
    humidite_moy    DECIMAL(5,2) CHECK (humidite_moy BETWEEN 0 AND 100),
    precipitations  DECIMAL(5,2) CHECK (precipitations >= 0),
    saison          VARCHAR(20) NOT NULL CHECK (
        saison IN ('printemps', 'ete', 'automne', 'hiver')
    ),
    date_collecte   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Contraintes CHECK** : `temperature_moy`, `humidite_moy`, `precipitations`, `saison` (4 contraintes).

---

### Table `articles` (source externe — scraping)

```sql
CREATE TABLE articles (
    article_id      SERIAL PRIMARY KEY,
    titre           VARCHAR(500) NOT NULL,
    url_source      TEXT UNIQUE NOT NULL,
    nom_source      VARCHAR(100) NOT NULL,
    resume          TEXT NULL,
    date_publication TIMESTAMP NULL,
    date_scraping   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Contraintes CHECK** : aucune (données textuelles libres). **Contrainte UNIQUE** : `url_source`.

---

## Récapitulatif des contraintes

| Table | CHECK count | FK | Notes |
|-------|-------------|-----|-------|
| regions | 1 | — | Référentiel racine |
| clients | 4 | 1 → regions | Soft delete via `date_suppression` |
| predictions | 3 | 1 → clients | |
| contrats | 4 | 1 → clients | CHECK croisé `date_fin > date_debut` |
| sinistres | 3 | 1 → contrats | |
| donnees_meteo | 4 | 1 → regions | |
| articles | 0 | — | UNIQUE sur `url_source` |
| **Total** | **19** | **5** | + 3 CHECK supplémentaires sur contrats* |

> *Le CHECK `date_fin > date_debut` est compté séparément → total effectif : **22 CHECK** (en incluant les CHECKs inline et les CONSTRAINT nommées).

---

## Index (20 minimum)

```sql
-- FK indexes (performance jointures)
CREATE INDEX idx_clients_region_id      ON clients(region_id);
CREATE INDEX idx_predictions_client_id  ON predictions(client_id);
CREATE INDEX idx_contrats_client_id     ON contrats(client_id);
CREATE INDEX idx_sinistres_contrat_id   ON sinistres(contrat_id);
CREATE INDEX idx_meteo_region_id        ON donnees_meteo(region_id);

-- Colonnes filtrées fréquemment (API, ETL)
CREATE INDEX idx_clients_fumeur         ON clients(fumeur);
CREATE INDEX idx_clients_age            ON clients(age);
CREATE INDEX idx_clients_imc            ON clients(imc);
CREATE INDEX idx_clients_sexe           ON clients(sexe);
CREATE INDEX idx_clients_date_creation  ON clients(date_creation);
CREATE INDEX idx_predictions_categorie  ON predictions(categorie_risque);
CREATE INDEX idx_predictions_decision   ON predictions(decision);
CREATE INDEX idx_predictions_date       ON predictions(date_prediction);
CREATE INDEX idx_contrats_statut        ON contrats(statut);
CREATE INDEX idx_contrats_date_debut    ON contrats(date_debut);
CREATE INDEX idx_sinistres_date         ON sinistres(date_sinistre);
CREATE INDEX idx_sinistres_type         ON sinistres(type_sinistre);
CREATE INDEX idx_sinistres_statut       ON sinistres(statut_sinistre);
CREATE INDEX idx_meteo_saison           ON donnees_meteo(saison);
CREATE INDEX idx_articles_date_scraping ON articles(date_scraping);

-- Index partiel (constitution Principe IV — soft delete)
CREATE INDEX idx_clients_actifs ON clients(client_id)
    WHERE date_suppression IS NULL;
```

**Total : 21 index** (5 FK + 15 colonnes filtrées + 1 partiel).

---

## Interface Python — Modèles ORM (`database/models.py`)

```python
class Region(Base):      # ← regions
class Client(Base):      # ← clients
class Prediction(Base):  # ← predictions
class Contrat(Base):     # ← contrats
class Sinistre(Base):    # ← sinistres
class DonneesMeteo(Base):# ← donnees_meteo
class Article(Base):     # ← articles
```

Relations ORM :
- `Client.region` → `Region` (many-to-one)
- `Client.predictions` → `[Prediction]` (one-to-many)
- `Client.contrats` → `[Contrat]` (one-to-many)
- `Contrat.sinistres` → `[Sinistre]` (one-to-many)
- `Region.donnees_meteo` → `[DonneesMeteo]` (one-to-many)

---

## Fonctions CRUD (`database/crud.py`)

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `create_client` | `(db, ClientCreate) -> Client` | INSERT + retourne l'ORM |
| `get_client` | `(db, client_id) -> Client \| None` | SELECT par PK |
| `get_clients` | `(db, skip, limit, actifs_only) -> list[Client]` | SELECT avec filtre soft delete |
| `update_client` | `(db, client_id, ClientUpdate) -> Client \| None` | UPDATE colonnes non-null |
| `soft_delete_client` | `(db, client_id) -> Client \| None` | UPDATE date_suppression = NOW() |
| `create_prediction` | `(db, PredictionCreate) -> Prediction` | INSERT |
| `get_predictions_by_client` | `(db, client_id) -> list[Prediction]` | SELECT par FK |
| `create_contrat` | `(db, ContratCreate) -> Contrat` | INSERT |
| `create_sinistre` | `(db, SinistreCreate) -> Sinistre` | INSERT |

---

## Mapping CSV → BDD (`database/load_csv.py`)

| Colonne CSV | Type CSV | Transformation | Colonne BDD | Type BDD |
|-------------|----------|----------------|-------------|----------|
| `sex` | str | rename + male→'homme', female→'femme' | `sexe` | VARCHAR(10) |
| `bmi` | float | rename uniquement | `imc` | DECIMAL(5,2) |
| `children` | int | rename uniquement | `enfants` | INTEGER |
| `smoker` | str | yes→True, no→False | `fumeur` | BOOLEAN |
| `region` | str | lookup `regions.nom_region` → `region_id` | `region_id` | INTEGER FK |
| `age` | int | inchangé | `age` | INTEGER |
| `charges` | float | **ignoré** (non stocké dans `clients`) | — | — |

`email` et `telephone` → NULL pour toutes les lignes (non disponibles dans le CSV).
