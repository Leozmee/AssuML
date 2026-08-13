-- ============================================================
-- AssuML — Schéma PostgreSQL complet
-- 7 tables, 22 contraintes CHECK, 21 index, 5 FK CASCADE
-- Idempotent : DROP IF EXISTS dans l'ordre inverse des FK
-- ============================================================

-- ── Suppression dans l'ordre inverse des FK ───────────────────
DROP TABLE IF EXISTS contrats       CASCADE;
DROP TABLE IF EXISTS predictions    CASCADE;
DROP TABLE IF EXISTS clients        CASCADE;
DROP TABLE IF EXISTS donnees_meteo    CASCADE;
DROP TABLE IF EXISTS stats_regionales CASCADE;
DROP TABLE IF EXISTS articles         CASCADE;
DROP TABLE IF EXISTS regions          CASCADE;

-- ============================================================
-- TABLE : regions (référentiel racine)
-- ============================================================
CREATE TABLE regions (
    region_id   SERIAL PRIMARY KEY,
    nom_region  VARCHAR(50) UNIQUE NOT NULL,
    CONSTRAINT chk_regions_nom CHECK (
        nom_region IN ('southwest', 'southeast', 'northwest', 'northeast')
    )
);

-- Pré-remplissage des 4 régions
INSERT INTO regions (nom_region) VALUES
    ('southwest'),
    ('southeast'),
    ('northwest'),
    ('northeast');

-- ============================================================
-- TABLE : clients (soft delete via date_suppression)
-- ============================================================
CREATE TABLE clients (
    client_id        SERIAL PRIMARY KEY,
    nom              VARCHAR(100) NULL,  -- NULL pour les clients seedés (insurance.csv)
    prenom           VARCHAR(100) NULL,  -- obligatoire pour tout nouveau client créé via l'app
    region_id        INTEGER NOT NULL
                     REFERENCES regions(region_id) ON DELETE CASCADE,
    age              INTEGER NOT NULL
                     CHECK (age BETWEEN 18 AND 120),
    sexe             VARCHAR(10) NOT NULL
                     CHECK (sexe IN ('homme', 'femme')),
    imc              DECIMAL(5, 2) NOT NULL
                     CHECK (imc BETWEEN 10.00 AND 80.00),
    enfants          INTEGER NOT NULL DEFAULT 0
                     CHECK (enfants >= 0),
    fumeur           BOOLEAN NOT NULL DEFAULT FALSE,
    a_un_compte      BOOLEAN NOT NULL DEFAULT FALSE,
    email            VARCHAR(255) NULL,
    telephone        VARCHAR(20)  NULL,
    date_creation    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_suppression TIMESTAMP NULL  -- NULL = actif, valeur = supprimé logiquement
);

-- ============================================================
-- TABLE : predictions
-- ============================================================
CREATE TABLE predictions (
    prediction_id    SERIAL PRIMARY KEY,
    client_id        INTEGER NOT NULL
                     REFERENCES clients(client_id) ON DELETE CASCADE,
    cout_predit      DECIMAL(10, 2),
    score_risque     DECIMAL(5, 4)
                     CHECK (score_risque BETWEEN 0 AND 1),
    categorie_risque VARCHAR(20)
                     CHECK (categorie_risque IN ('faible', 'moyen', 'eleve', 'critique')),
    decision         VARCHAR(20)
                     CHECK (decision IN ('accepter', 'refuser', 'examiner')),
    prime            DECIMAL(10, 2),
    version_modele   VARCHAR(60),
    date_prediction  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE : contrats
-- ============================================================
CREATE TABLE contrats (
    contrat_id      SERIAL PRIMARY KEY,
    client_id       INTEGER NOT NULL
                    REFERENCES clients(client_id) ON DELETE CASCADE,
    statut          VARCHAR(20) NOT NULL DEFAULT 'actif'
                    CHECK (statut IN ('actif', 'resilie', 'expire', 'suspendu')),
    prime_mensuelle DECIMAL(10, 2) NOT NULL
                    CHECK (prime_mensuelle > 0),
    date_debut      DATE NOT NULL DEFAULT CURRENT_DATE,
    date_fin        DATE NULL,
    type_couverture VARCHAR(50) NOT NULL
                    CHECK (type_couverture IN ('basique', 'standard', 'premium', 'famille')),
    date_creation   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_contrats_dates CHECK (date_fin IS NULL OR date_fin > date_debut)
);

-- ============================================================
-- TABLE : donnees_meteo (source externe — API OpenWeatherMap)
-- ============================================================
CREATE TABLE donnees_meteo (
    meteo_id        SERIAL PRIMARY KEY,
    region_id       INTEGER NOT NULL
                    REFERENCES regions(region_id) ON DELETE CASCADE,
    temperature_moy DECIMAL(5, 2)
                    CHECK (temperature_moy BETWEEN -50 AND 60),
    humidite_moy    DECIMAL(5, 2)
                    CHECK (humidite_moy BETWEEN 0 AND 100),
    precipitations  DECIMAL(5, 2)
                    CHECK (precipitations >= 0),
    saison          VARCHAR(20) NOT NULL
                    CHECK (saison IN ('printemps', 'ete', 'automne', 'hiver')),
    date_collecte   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE : stats_regionales (source externe — BDD SQLite data/external/stats_regionales.db)
-- ============================================================
CREATE TABLE stats_regionales (
    stats_id            SERIAL PRIMARY KEY,
    region_id           INTEGER NOT NULL
                         REFERENCES regions(region_id) ON DELETE CASCADE,
    taux_obesite        DECIMAL(5, 2)
                         CHECK (taux_obesite BETWEEN 0 AND 100),
    taux_tabagisme       DECIMAL(5, 2)
                         CHECK (taux_tabagisme BETWEEN 0 AND 100),
    esperance_vie        DECIMAL(5, 2)
                         CHECK (esperance_vie > 0),
    taux_diabete         DECIMAL(5, 2)
                         CHECK (taux_diabete BETWEEN 0 AND 100),
    medecins_pour_100k   DECIMAL(6, 2)
                         CHECK (medecins_pour_100k > 0),
    taux_non_assures     DECIMAL(5, 2)
                         CHECK (taux_non_assures BETWEEN 0 AND 100),
    date_extraction      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE : articles (source externe — scraping)
-- ============================================================
CREATE TABLE articles (
    article_id       SERIAL PRIMARY KEY,
    titre            VARCHAR(500) NOT NULL,
    url_source       TEXT UNIQUE NOT NULL,
    nom_source       VARCHAR(100) NOT NULL,
    resume           TEXT NULL,
    image_url        TEXT NULL,
    date_publication TIMESTAMP NULL,
    date_scraping    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEX (22 au total)
-- ============================================================

-- Index sur les clés étrangères (jointures)
CREATE INDEX idx_clients_region_id      ON clients(region_id);
CREATE INDEX idx_predictions_client_id  ON predictions(client_id);
CREATE INDEX idx_contrats_client_id     ON contrats(client_id);
CREATE INDEX idx_meteo_region_id        ON donnees_meteo(region_id);
CREATE INDEX idx_stats_regionales_region_id ON stats_regionales(region_id);

-- Index sur les colonnes filtrées fréquemment (API + ETL)
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
CREATE INDEX idx_meteo_saison           ON donnees_meteo(saison);
CREATE INDEX idx_articles_date_scraping ON articles(date_scraping);

-- Index partiel sur les clients actifs (constitution Principe IV — soft delete)
CREATE INDEX idx_clients_actifs ON clients(client_id)
    WHERE date_suppression IS NULL;
