# Feature Specification: Base de Données PostgreSQL — Schéma & Couche d'Accès

**Feature Branch**: `005-postgres-db-setup`
**Created**: 2026-05-04
**Status**: Draft

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Schéma de base de données opérationnel (Priority: P1)

Un développeur ou un administrateur veut que la base de données `assuml_db` soit prête à l'emploi :
toutes les tables existent avec leurs contraintes, les régions sont pré-remplies, et le schéma
peut être recréé de zéro en rejouant un seul fichier SQL.

**Why this priority** : Toutes les autres features (API, ETL, Streamlit) dépendent de ce socle.
Sans base de données fonctionnelle, rien ne peut être persisté ni testé en intégration.

**Independent Test** : Exécuter `database/schema.sql` sur une base vide → les 7 tables sont créées,
les 4 régions existent dans `regions`, toutes les contraintes CHECK sont actives, tous les index sont présents.

**Acceptance Scenarios** :

1. **Given** une base PostgreSQL vide, **When** on exécute `schema.sql`, **Then** les 7 tables sont créées sans erreur, `regions` contient exactement 4 lignes, et une insertion avec un âge hors [18–120] est rejetée par la base.
2. **Given** la base initialisée, **When** on insère un `client` lié à une région puis qu'on supprime cette région, **Then** le client est supprimé automatiquement (ON DELETE CASCADE).
3. **Given** la base déjà initialisée, **When** on rejoue `schema.sql` (DROP IF EXISTS + CREATE), **Then** le schéma est recréé proprement sans erreur ni conflit.

---

### User Story 2 — Couche d'accès Python (ORM + CRUD) (Priority: P1)

Un développeur Python peut interagir avec la base via des fonctions nommées, sans écrire de SQL brut.
La configuration de connexion est lue depuis un fichier `.env` — aucun credential dans le code source.

**Why this priority** : L'API FastAPI et les pipelines ETL consomment directement ces fonctions.
Sans couche d'accès unifiée, chaque composant réinvente sa propre connexion, créant des incohérences.

**Independent Test** : Appeler `create_client(...)` → un enregistrement apparaît dans `clients`.
Appeler `soft_delete_client(id)` → `date_suppression` est renseignée, le client disparaît de `get_clients()`.

**Acceptance Scenarios** :

1. **Given** une connexion valide, **When** on appelle `create_client(age=30, sexe='homme', imc=22.5, enfants=1, fumeur=False, region_id=1)`, **Then** un `client_id` est retourné et la ligne est visible dans la base.
2. **Given** un client existant, **When** on appelle `soft_delete_client(client_id)`, **Then** `date_suppression` est définie à l'horodatage courant, et `get_clients()` ne retourne plus ce client.
3. **Given** des credentials incorrects dans `.env`, **When** on initialise la connexion, **Then** une erreur explicite est levée sans exposer le mot de passe dans les messages d'erreur.

---

### User Story 3 — Chargement des données historiques CSV (Priority: P2)

Les 1 338 lignes de `insurance.csv` sont chargées dans la table `clients` avec les transformations
de nommage nécessaires. La table `regions` sert de référentiel pour résoudre les clés étrangères.

**Why this priority** : Les démonstrations, les tests d'intégration et les développements Streamlit
nécessitent des données réalistes. Sans ce chargement, la base reste vide après le déploiement.

**Independent Test** : Après le chargement, compter les lignes dans `clients` → 1338.
Filtrer par `fumeur = TRUE` → le nombre correspond exactement aux `smoker='yes'` du CSV.

**Acceptance Scenarios** :

1. **Given** `insurance.csv` et une base avec les 4 régions, **When** on exécute le script de chargement, **Then** 1338 lignes sont insérées dans `clients` sans erreur, `email` et `telephone` sont NULL pour toutes.
2. **Given** les 1338 clients chargés, **When** on filtre par `fumeur = TRUE`, **Then** le nombre retourné correspond aux lignes `smoker='yes'` du CSV.
3. **Given** le script lancé une deuxième fois, **When** la table n'est pas vide, **Then** le script effectue un TRUNCATE avant insertion (pas de doublons) et le résultat final est toujours 1338 lignes.

---

### Edge Cases

- Tentative d'insertion d'un `client` avec une `region_id` inexistante → rejet par contrainte FK.
- Insertion d'un `sinistre` avec `montant_sinistre = 0` → rejet par CHECK > 0.
- Insertion d'un `contrat` avec `date_fin` ≤ `date_debut` → rejet par CHECK.
- Exécution du chargement CSV deux fois sans TRUNCATE → doublons détectés, message explicite.
- Connexion à la base sans que PostgreSQL soit démarré → message d'erreur clair, pas de crash silencieux.
- Score de risque hors [0, 1] dans `predictions` → rejet par CHECK.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** : La base `assuml_db` doit contenir exactement 7 tables nommées en français : `regions`, `clients`, `predictions`, `contrats`, `sinistres`, `donnees_meteo`, `articles`.
- **FR-002** : Les 5 clés étrangères doivent toutes être configurées `ON DELETE CASCADE`.
- **FR-003** : La table `regions` doit être pré-remplie avec les 4 valeurs : `southwest`, `southeast`, `northwest`, `northeast`.
- **FR-004** : La table `clients` doit supporter le soft delete via `date_suppression` (NULL = actif, valeur = supprimé logiquement).
- **FR-005** : Les suppressions de clients doivent toujours être des soft deletes — aucun DELETE physique ne doit être exécuté sur `clients`.
- **FR-006** : Le schéma doit inclure au moins 20 index : sur chaque FK, sur les colonnes fréquemment filtrées (`fumeur`, `categorie_risque`, `statut`), et un index partiel sur les clients actifs (`WHERE date_suppression IS NULL`).
- **FR-007** : Toute configuration de connexion (hôte, port, utilisateur, mot de passe, nom de base) doit être lue depuis des variables d'environnement, jamais hardcodée dans le code source.
- **FR-008** : La couche d'accès doit exposer les fonctions : `create_client`, `get_client`, `get_clients`, `update_client`, `soft_delete_client`, `create_prediction`, `get_predictions_by_client`, `create_contrat`, `create_sinistre`.
- **FR-009** : Le script de chargement doit transformer : `sex` → `sexe` (male→homme, female→femme), `bmi` → `imc`, `children` → `enfants`, `smoker` → `fumeur` (yes→True, no→False), `region` → `region_id` via lookup dans `regions`.
- **FR-010** : Le fichier `schema.sql` doit être idempotent (`DROP TABLE IF EXISTS` + `CREATE TABLE`).
- **FR-011** : Un fichier `.env.example` doit documenter toutes les variables d'environnement nécessaires sans valeurs réelles.

### Key Entities

- **regions** : Référentiel des 4 zones géographiques USA. Racine de l'arbre de clés étrangères.
- **clients** : Profil assuré (âge, sexe, IMC, enfants, fumeur, région). Supporte le soft delete.
- **predictions** : Résultat d'une demande ML (coût prédit, catégorie, décision, prime, version modèle).
- **contrats** : Contrat d'assurance souscrit (statut, couverture, dates, prime mensuelle).
- **sinistres** : Événement de sinistre rattaché à un contrat (montant, type, statut).
- **donnees_meteo** : Données météo par région et par saison (source API externe).
- **articles** : Articles de presse scrappés sur la santé et l'assurance (source scraping externe).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** : L'exécution de `schema.sql` sur une base vide complète sans erreur en moins de 10 secondes.
- **SC-002** : Les 22 contraintes CHECK sont toutes actives — chaque contrainte rejette au moins une valeur invalide lors d'un test manuel.
- **SC-003** : Le chargement des 1338 lignes CSV complète en moins de 30 secondes avec zéro ligne perdue ou rejetée.
- **SC-004** : Chaque fonction CRUD produit le résultat attendu (enregistrement créé, liste filtrée, soft delete visible) sans erreur sur des données valides.
- **SC-005** : La lecture d'un client par son identifiant sur la base chargée (1338 lignes) prend moins de 100ms.
- **SC-006** : Un fichier `.env.example` documentant les 5 variables de connexion est présent et commité.

---

## Assumptions

- PostgreSQL est installé via Homebrew sur macOS (`brew install postgresql@15`) — pas de Docker pour cette feature.
- L'utilisateur dédié PostgreSQL se nommera `assuml_user` avec un mot de passe défini dans `.env`.
- Le fichier `.env` est déjà dans `.gitignore` (constitution Principe IV — aucun credential commité).
- Le script de chargement CSV est un script Python standalone (`database/load_csv.py`), déclenché manuellement.
- Le chargement est idempotent via TRUNCATE + INSERT (pas de migration incrémentale pour cette feature).
- Les colonnes `email` et `telephone` de `clients` seront NULL pour toutes les lignes du CSV (non disponibles dans `insurance.csv`).
- `database/schema.sql`, `database/connection.py`, `database/models.py`, `database/crud.py`, `database/load_csv.py` sont tous commitables (aucun credential).
- Cette feature ne couvre pas les migrations de schéma (Alembic) — c'est prévu pour la feature API.
