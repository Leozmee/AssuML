---

description: "Liste de tâches — Base de Données PostgreSQL — Schéma & Couche d'Accès"
---

# Tasks: Base de Données PostgreSQL — Schéma & Couche d'Accès

**Input**: Documents de conception dans `specs/005-postgres-db-setup/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Inclus — requis par la constitution (Principe V).
Tests unitaires dans `tests/unit/test_crud.py` (SQLite in-memory).
Tests d'intégration dans `tests/integration/test_db_connection.py` (PostgreSQL réel, marqués `@pytest.mark.integration`).

**Organisation**: 3 User Stories — schéma SQL (US1, P1), couche Python ORM+CRUD (US2, P1), chargement CSV (US3, P2).

## Format: `[ID] [P?] [Story?] Description — fichier cible`

---

## Phase 1 : Setup

**But**: Créer la structure de répertoires, le `.env.example`, et vérifier les prérequis PostgreSQL.

- [ ] T001 Créer `database/__init__.py` (module vide) et le répertoire `scripts/` à la racine du projet
- [ ] T002 [P] Créer `.env.example` avec les 5 variables : `DB_HOST=localhost`, `DB_PORT=5432`, `DB_NAME=assuml_db`, `DB_USER=assuml_user`, `DB_PASS=assuml_pass` — fichier `.env.example`
- [ ] T003 [P] Vérifier que `.env` est dans `.gitignore` ; vérifier que PostgreSQL 15+ est installé (`psql --version`) et que la base `assuml_db` + l'utilisateur `assuml_user` existent (commandes dans `quickstart.md`)

**Checkpoint** : répertoire `database/` présent, `.env.example` commité, `.env` gitignored, PostgreSQL accessible.

---

## Phase 2 : Fondation (Prérequis bloquants)

**But**: Aucun prérequis bloquant supplémentaire au-delà du Setup.

**⚠️ ORDRE STRICT intra-feature** :
- US1 (schema.sql) → US2 (ORM + CRUD, qui lit les tables existantes pour les modèles)
- US2 → US3 (load_csv.py utilise la session SQLAlchemy de connection.py)
- US1 + US2 → `scripts/setup_db.py` (orchestre les deux)

---

## Phase 3 : User Story 1 — Schéma SQL opérationnel (Priority: P1) 🎯 MVP

**But**: Créer `database/schema.sql` avec les 7 tables, 22 contraintes CHECK, 21 index, soft delete,
5 FK CASCADE, et les 4 régions pré-remplies. Exécuter le fichier et valider.

**Test indépendant** : `psql -U assuml_user -d assuml_db -f database/schema.sql` sans erreur.
Vérifier `\dt` → 7 tables. `SELECT COUNT(*) FROM regions` → 4. Tenter une insertion avec age=15 → rejetée par CHECK.

### Implémentation US1

- [ ] T004 [US1] Créer `database/schema.sql` — en-tête avec `DROP TABLE IF EXISTS ... CASCADE` pour les 7 tables (ordre inverse des FK : sinistres, contrats, predictions, clients, donnees_meteo, articles, regions), puis table `regions` (SERIAL PK, nom_region VARCHAR(50) UNIQUE NOT NULL, CHECK IN ('southwest','southeast','northwest','northeast')) + `INSERT INTO regions` des 4 valeurs
- [ ] T005 [US1] Ajouter table `clients` dans `database/schema.sql` — colonnes : `client_id SERIAL PK`, `region_id INTEGER NOT NULL REFERENCES regions ON DELETE CASCADE`, `age INTEGER NOT NULL CHECK(age BETWEEN 18 AND 120)`, `sexe VARCHAR(10) NOT NULL CHECK(sexe IN ('homme','femme'))`, `imc DECIMAL(5,2) NOT NULL CHECK(imc BETWEEN 10 AND 80)`, `enfants INTEGER NOT NULL DEFAULT 0 CHECK(enfants >= 0)`, `fumeur BOOLEAN NOT NULL DEFAULT FALSE`, `email VARCHAR(255) NULL`, `telephone VARCHAR(20) NULL`, `date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP`, `date_suppression TIMESTAMP NULL`
- [ ] T006 [US1] Ajouter tables `predictions` et `contrats` dans `database/schema.sql` — `predictions` : PK, FK clients CASCADE, `cout_predit DECIMAL(10,2)`, `score_risque DECIMAL(5,4) CHECK(0..1)`, `categorie_risque VARCHAR(20) CHECK(faible/moyen/eleve/critique)`, `decision VARCHAR(20) CHECK(accepter/refuser/examiner)`, `prime DECIMAL(10,2)`, `version_modele VARCHAR(20)`, `date_prediction TIMESTAMP DEFAULT NOW()` ; `contrats` : PK, FK clients CASCADE, `statut VARCHAR(20) DEFAULT 'actif' CHECK(actif/resilie/expire/suspendu)`, `prime_mensuelle DECIMAL(10,2) CHECK(>0)`, `date_debut DATE DEFAULT CURRENT_DATE`, `date_fin DATE NULL`, `type_couverture VARCHAR(50) CHECK(basique/standard/premium/famille)`, `date_creation TIMESTAMP`, `CONSTRAINT chk_contrats_dates CHECK(date_fin IS NULL OR date_fin > date_debut)`
- [ ] T007 [US1] Ajouter tables `sinistres`, `donnees_meteo`, `articles` dans `database/schema.sql` — `sinistres` : PK, FK contrats CASCADE, `date_sinistre DATE NOT NULL`, `montant_sinistre DECIMAL(10,2) CHECK(>0)`, `type_sinistre VARCHAR(50) CHECK(hospitalisation/consultation/pharmacie/chirurgie/urgence/autre)`, `statut_sinistre VARCHAR(20) DEFAULT 'en_cours' CHECK(en_cours/accepte/refuse/rembourse)`, `description TEXT NULL` ; `donnees_meteo` : PK, FK regions CASCADE, `temperature_moy CHECK(-50..60)`, `humidite_moy CHECK(0..100)`, `precipitations CHECK(>=0)`, `saison CHECK(printemps/ete/automne/hiver)`, `date_collecte TIMESTAMP` ; `articles` : PK, `titre VARCHAR(500)`, `url_source TEXT UNIQUE NOT NULL`, `nom_source VARCHAR(100)`, `resume TEXT NULL`, `date_publication TIMESTAMP NULL`, `date_scraping TIMESTAMP DEFAULT NOW()`
- [ ] T008 [US1] Ajouter les 21 index dans `database/schema.sql` — 5 index FK (`idx_clients_region_id`, `idx_predictions_client_id`, `idx_contrats_client_id`, `idx_sinistres_contrat_id`, `idx_meteo_region_id`), 15 index colonnes filtrées (`idx_clients_fumeur/age/imc/sexe/date_creation`, `idx_predictions_categorie/decision/date`, `idx_contrats_statut/date_debut`, `idx_sinistres_date/type/statut`, `idx_meteo_saison`, `idx_articles_date_scraping`), 1 index partiel `idx_clients_actifs ON clients(client_id) WHERE date_suppression IS NULL`
- [ ] T009 [US1] Exécuter `psql -U assuml_user -d assuml_db -f database/schema.sql` et valider : `\dt` → 7 tables, `SELECT COUNT(*) FROM regions` → 4, tenter `INSERT INTO clients(region_id,age,...) VALUES(1,15,...)` → erreur CHECK age, tenter `INSERT INTO clients(region_id,age,...) VALUES(999,30,...)` → erreur FK

**Checkpoint** : US1 complète — schéma PostgreSQL opérationnel, toutes contraintes actives, rejouable sans erreur.

---

## Phase 4 : User Story 2 — Couche d'accès Python ORM + CRUD (Priority: P1)

**But**: Créer `database/connection.py` (engine + sessionmaker + get_db), `database/models.py`
(7 modèles ORM SQLAlchemy 2.0), `database/crud.py` (9 fonctions CRUD avec soft delete).

**Test indépendant** : `pytest tests/unit/test_crud.py -v` → tous PASSED (SQLite in-memory, sans PostgreSQL).
`pytest tests/integration/test_db_connection.py -v -m integration` → connexion + CRUD sur PostgreSQL réel.

### Tests US2

- [ ] T010 [P] [US2] Créer `tests/unit/test_crud.py` — engine SQLite in-memory, créer les tables via `Base.metadata.create_all`, tester : `test_create_client` (retourne Client avec client_id), `test_get_client` (retrouve par PK), `test_get_clients_actifs_only` (filtre date_suppression IS NULL), `test_soft_delete_client` (date_suppression définie, client absent de get_clients), `test_create_prediction` (retourne Prediction), `test_get_predictions_by_client` (liste par client_id), `test_create_contrat`, `test_create_sinistre`
- [ ] T011 [P] [US2] Créer `tests/integration/test_db_connection.py` — marqués `@pytest.mark.integration`, tester connexion `engine.connect()`, tester `SELECT COUNT(*) FROM regions` → 4, tester création + lecture d'un client sur PostgreSQL réel

### Implémentation US2

- [ ] T012 [US2] Créer `database/connection.py` — `load_dotenv()`, construire `DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"`, `engine = create_engine(DATABASE_URL)`, `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`, `def get_db(): db = SessionLocal(); try: yield db; finally: db.close()`
- [ ] T013 [US2] Créer `database/models.py` — `class Base(DeclarativeBase): pass`, puis 7 classes : `Region` (region_id, nom_region, relation → clients + donnees_meteo), `Client` (toutes colonnes + relation → region, predictions, contrats), `Prediction` (toutes colonnes + relation → client), `Contrat` (toutes colonnes + relation → client, sinistres), `Sinistre` (toutes colonnes + relation → contrat), `DonneesMeteo` (toutes colonnes + relation → region), `Article` (toutes colonnes) — utiliser `Mapped[T]`, `mapped_column`, `relationship`, `CheckConstraint`
- [ ] T014 [US2] Créer `database/crud.py` — fonctions : `create_client(db, age, sexe, imc, enfants, fumeur, region_id, email=None, telephone=None) -> Client`, `get_client(db, client_id) -> Client | None`, `get_clients(db, skip=0, limit=100, actifs_only=True) -> list[Client]` (filtre `date_suppression IS NULL` si actifs_only), `update_client(db, client_id, **kwargs) -> Client | None`, `soft_delete_client(db, client_id) -> Client | None` (UPDATE date_suppression = datetime.now(), jamais DELETE)
- [ ] T015 [US2] Ajouter dans `database/crud.py` — fonctions : `create_prediction(db, client_id, cout_predit, score_risque, categorie_risque, decision, prime, version_modele) -> Prediction`, `get_predictions_by_client(db, client_id) -> list[Prediction]`, `create_contrat(db, client_id, statut, prime_mensuelle, date_debut, type_couverture, date_fin=None) -> Contrat`, `create_sinistre(db, contrat_id, date_sinistre, montant_sinistre, type_sinistre, statut_sinistre='en_cours', description=None) -> Sinistre`
- [ ] T016 [US2] Exécuter `pytest tests/unit/test_crud.py -v` → tous PASSED ; exécuter `pytest tests/integration/test_db_connection.py -v -m integration` → PASSED

**Checkpoint** : US2 complète — couche Python opérationnelle, tests unitaires et intégration PASSED.

---

## Phase 5 : User Story 3 — Chargement des données historiques CSV (Priority: P2)

**But**: Créer `database/load_csv.py` (TRUNCATE + INSERT 1338 lignes avec mapping colonnes)
et `scripts/setup_db.py` (orchestre tout : connexion → schema → chargement → rapport).

**Test indépendant** : `python scripts/setup_db.py` sans erreur.
`SELECT COUNT(*) FROM clients` → 1338. `SELECT COUNT(*) FROM clients WHERE fumeur = TRUE` → correspond aux `smoker='yes'` du CSV.

### Implémentation US3

- [ ] T017 [US3] Créer `database/load_csv.py` — docstring français, charger `data/small_data/insurance.csv`, appeler `rename_columns()` de `data_pipeline.transform.cleaning` pour sex→sexe/bmi→imc/children→enfants/smoker→fumeur, puis appliquer : `sexe` male→'homme' female→'femme', `fumeur` yes→True no→False, `region` string→region_id via `SELECT region_id FROM regions WHERE nom_region = ?`, email/telephone=NULL pour toutes les lignes, `TRUNCATE TABLE clients RESTART IDENTITY CASCADE` avant INSERT, INSERT en batch avec `db.bulk_insert_mappings(Client, rows)`, afficher `✅ {n} clients chargés`
- [ ] T018 [US3] Créer `scripts/setup_db.py` — orchestrer : (1) tester connexion `engine.connect()` → `✅ Connexion OK`, (2) lire `database/schema.sql` et l'exécuter via `psycopg2.connect()` + `cursor.execute()` → `✅ Schéma créé`, (3) appeler `load_csv.main()` → `✅ 1338 clients chargés`, (4) afficher rapport COUNT(*) pour chacune des 7 tables
- [ ] T019 [US3] Exécuter `python scripts/setup_db.py` et valider : 1338 clients, 4 régions, rapport complet affiché sans erreur ; exécuter une deuxième fois → même résultat (idempotence via TRUNCATE)

**Checkpoint** : US3 complète — 1338 clients chargés, setup_db.py rejouable, rapport de validation affiché.

---

## Phase finale : Polish & Conformité

- [ ] T020 [P] PEP8 + black sur `database/` et `scripts/` : `flake8 database/ scripts/ --max-line-length=88 && black database/ scripts/`
- [ ] T021 [P] Vérifier `git status` — `.env` absent (gitignored), `database/schema.sql` présent, `.env.example` présent
- [ ] T022 Vérifier idempotence complète : exécuter `python scripts/setup_db.py` deux fois de suite → même résultat final, aucune erreur de contrainte ou de séquence

---

## Dépendances et ordre d'exécution

### Dépendances entre phases

- **Phase 1 (Setup)** : Aucune — démarre immédiatement.
- **US1 (Phase 3)** : Dépend de Phase 1 (PostgreSQL accessible, `.env` configuré).
- **US2 (Phase 4)** : Dépend de US1 — les modèles ORM reflètent le schéma existant.
- **US3 (Phase 5)** : Dépend de US1 + US2 — load_csv utilise Session + modèles ; setup_db orchestre schema + load.
- **Polish** : Dépend de US1 + US2 + US3.

### Opportunités de parallélisme

- **Phase 1** : T002 ‖ T003 (fichiers distincts, vérifications indépendantes).
- **US2** : T010 (test_crud.py) ‖ T011 (test_db_connection.py) ‖ T012 (connection.py) ‖ T013 (models.py) — tous fichiers distincts, peuvent démarrer ensemble.
- **Polish** : T020 ‖ T021 en parallèle.

---

## Exemple de parallélisme

### US2 — Couche Python (fichiers tous distincts)

```bash
# Simultanément :
Task: "Créer tests/unit/test_crud.py"              # T010
Task: "Créer tests/integration/test_db_connection.py"  # T011
Task: "Créer database/connection.py"               # T012
Task: "Créer database/models.py"                   # T013
# Puis séquentiellement :
Task: "Créer database/crud.py — partie 1"          # T014
Task: "Ajouter crud.py — partie 2"                 # T015
Task: "pytest tests/ → PASSED"                     # T016
```

---

## Stratégie d'implémentation

### MVP First (US1 uniquement)

1. Phase 1 — Setup
2. US1 — `database/schema.sql` + exécution PostgreSQL (T004–T009)
3. **STOP et VALIDATION** : 7 tables créées, 4 régions, contraintes actives
4. Démo MVP : base PostgreSQL opérationnelle

### Livraison complète

1. Phase 1 → Setup OK
2. US1 → Schéma SQL validé sur PostgreSQL
3. US2 → ORM + CRUD → tests 100% PASSED
4. US3 → 1338 clients chargés → setup_db.py idempotent
5. Polish → flake8 + vérifications finales

---

## Notes

- `[P]` = peut s'exécuter en parallèle (fichiers distincts)
- `[USn]` = traçabilité vers la User Story dans spec.md
- **JAMAIS** de `DELETE` physique sur `clients` (constitution Principe IV) — uniquement `soft_delete_client` via `date_suppression`
- `schema.sql` commence TOUJOURS par les `DROP TABLE IF EXISTS` dans l'ordre inverse des FK
- Les tests unitaires (`test_crud.py`) utilisent SQLite in-memory — pas de dépendance PostgreSQL pour le CI
- Les tests d'intégration sont marqués `@pytest.mark.integration` et nécessitent un PostgreSQL actif
- `load_csv.py` réutilise `rename_columns()` de `cleaning.py` mais PAS `encode_categoricals()` (encodage ML ≠ encodage BDD)
