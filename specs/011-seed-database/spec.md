# Feature Specification: Seed Database — Clients initiaux

**Feature Branch**: `011-seed-database`
**Created**: 2026-06-13
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Démarrage Docker avec base peuplée (Priority: P1)

L'administrateur lance `docker compose up` pour la première fois. Sans aucune action manuelle, la base de données se remplit automatiquement avec les 4 régions et les 1 338 clients issus du dataset réel. L'assureur ouvre Streamlit et trouve immédiatement des clients disponibles pour le scoring et la gestion CRUD.

**Why this priority**: C'est le scénario de démonstration jury. Si la base est vide au démarrage, l'assureur ne peut rien scorer ni gérer — l'application perd son sens.

**Independent Test**: Exécuter `docker compose up`, attendre que le service seed se termine, puis vérifier via l'endpoint `/api/clients/` que la liste retourne 1 338 entrées.

**Acceptance Scenarios**:

1. **Given** une base PostgreSQL vide (tables créées, aucune donnée), **When** le service seed s'exécute, **Then** la table `regions` contient 4 lignes et la table `clients` contient 1 338 lignes.
2. **Given** le service seed a déjà été exécuté (base peuplée), **When** le service seed est relancé, **Then** aucun doublon n'est inséré et le script se termine avec le message "Base déjà peuplée, seed ignoré".
3. **Given** la base est peuplée, **When** l'assureur ouvre le module CRUD Streamlit, **Then** la liste des clients affiche des entrées avec âge, sexe, imc, région lisibles.

---

### User Story 2 — Données clients lisibles et métier (Priority: P2)

L'assureur consulte un client dans le module Scoring ou CRUD. Les données affichées sont en français et dans un format métier lisible : `sexe = "homme"`, `fumeur = true`, `region = "southwest"` — pas des valeurs encodées.

**Why this priority**: La lisibilité des données est essentielle pour la crédibilité de la démo. Des valeurs `0/1` ou des noms de colonnes anglais casseraient l'expérience assureur.

**Independent Test**: Appeler `GET /api/clients/1` et vérifier que `sexe` vaut `"homme"` ou `"femme"`, que `fumeur` est un booléen, que `region_id` correspond à une région existante.

**Acceptance Scenarios**:

1. **Given** le seed est exécuté, **When** on interroge un client dont `sex=male` dans le CSV, **Then** le champ `sexe` en base vaut `"homme"`.
2. **Given** le seed est exécuté, **When** on interroge un client dont `smoker=yes` dans le CSV, **Then** le champ `fumeur` en base vaut `true`.
3. **Given** le seed est exécuté, **When** on interroge un client dont `region=southwest` dans le CSV, **Then** le champ `region_id` correspond à l'entrée `southwest` de la table `regions`.

---

### User Story 3 — Table predictions vide au démarrage (Priority: P3)

L'assureur arrive sur l'application avec des clients mais sans prédictions pré-calculées. C'est lui qui décide quand scorer un client. Lorsqu'il clique "Scorer" dans le module Scoring, c'est la première et seule fois que le modèle ML tourne pour ce client.

**Why this priority**: Valide l'intégrité du flux métier et garantit que le jury voit les modèles ML travailler en direct, pas des résultats statiques.

**Independent Test**: Après le seed, appeler `GET /api/predictions/` et vérifier que la liste est vide. Puis scorer un client via Streamlit et vérifier qu'une ligne est insérée dans `predictions`.

**Acceptance Scenarios**:

1. **Given** le seed vient de s'exécuter, **When** on interroge la table `predictions`, **Then** elle est vide.
2. **Given** la table `predictions` est vide, **When** l'assureur clique "Scorer" sur le client 1, **Then** une ligne est insérée dans `predictions` avec `client_id=1`.

---

### Edge Cases

- Que se passe-t-il si `insurance.csv` est absent au démarrage du service seed ? → Le script échoue explicitement avec un message d'erreur clair (exit code non nul).
- Que se passe-t-il si la table `regions` est vide ? → Le script insère les 4 régions avant les clients.
- Que se passe-t-il si PostgreSQL n'est pas encore prêt quand le seed démarre ? → Le service Docker attend que postgres soit `healthy` avant de s'exécuter.
- Que se passe-t-il si le CSV contient une valeur de région inconnue ? → Le script loggue la ligne problématique et continue sans l'insérer.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** : Le script DOIT insérer les 4 régions (`southwest`, `southeast`, `northwest`, `northeast`) dans la table `regions` si elle est vide.
- **FR-002** : Le script DOIT lire `data/small_data/insurance.csv` et insérer les 1 338 lignes dans la table `clients`.
- **FR-003** : Le script DOIT transformer les valeurs anglaises du CSV en valeurs françaises métier : `sex` → `sexe` (male/female → homme/femme), `smoker` → `fumeur` (yes/no → true/false), `bmi` → `imc`, `children` → `enfants`.
- **FR-004** : Le script DOIT résoudre `region` (string) en `region_id` (integer FK) via lookup dans la table `regions`.
- **FR-005** : Le script DOIT être idempotent : si `clients` n'est pas vide, il ne fait rien et loggue "Base déjà peuplée, seed ignoré".
- **FR-006** : Le script DOIT laisser les tables `predictions`, `contrats`, `sinistres`, `articles`, `donnees_meteo` vides.
- **FR-007** : Le service Docker DOIT attendre que PostgreSQL soit `healthy` avant de lancer le seed.
- **FR-008** : Le service Docker DOIT s'exécuter une seule fois et se terminer proprement après insertion.
- **FR-009** : Le script DOIT logger le résultat final : nombre de régions et de clients insérés, ou message d'ignorance si déjà peuplé.
- **FR-010** : Le script DOIT échouer explicitement (exit code non nul) si `insurance.csv` est introuvable.

### Key Entities

- **Client** : personne assurée issue du dataset Kaggle. Attributs métier : âge, sexe, imc, nombre d'enfants, statut fumeur, région. Sans prédiction à la création.
- **Région** : référentiel géographique US à 4 valeurs fixes. Sert de clé étrangère pour les clients.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** : Après `docker compose up`, la table `clients` contient exactement 1 338 lignes en moins de 30 secondes après que PostgreSQL est prêt.
- **SC-002** : 100 % des clients insérés ont `sexe` dans `{homme, femme}`, `fumeur` en booléen, et un `region_id` valide référençant une des 4 régions.
- **SC-003** : La table `predictions` contient 0 ligne immédiatement après le seed.
- **SC-004** : Relancer le seed sur une base déjà peuplée ne crée aucun doublon et se termine en moins de 2 secondes.
- **SC-005** : L'assureur peut accéder à un client via le module CRUD Streamlit dans les 5 secondes suivant la fin du seed.

## Assumptions

- Le fichier `data/small_data/insurance.csv` est committé dans le dépôt et disponible dans le container Docker.
- La table `regions` est créée par `database/schema.sql` avant l'exécution du seed.
- Les 3 clients de test présents dans `schema.sql` (seed CI) ne sont pas présents en environnement Docker : le schéma Docker repart d'une base vide.
- `email` et `telephone` sont `NULL` pour tous les clients seedés (non présents dans le CSV).
- `date_creation` est valorisée à l'horodatage d'insertion (pas importée depuis le CSV).
- Le dataset `insurance.csv` ne contient pas de doublons — aucune déduplication nécessaire.
- La connexion PostgreSQL utilise les mêmes variables d'environnement que l'API FastAPI (`.env` / variables Docker Compose).
