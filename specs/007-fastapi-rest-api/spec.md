# Feature Specification: API REST FastAPI complète

**Feature Branch**: `007-fastapi-rest-api`
**Created**: 2026-05-04
**Status**: Draft
**Input**: API REST FastAPI avec 7 routers (clients, contrats, sinistres, articles, meteo, ml, stats), schémas Pydantic, prédictions ML avec scoring business, CORS Streamlit.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Gestion des clients via API (Priority: P1)

Un opérateur ou une application frontend peut créer, consulter, modifier et désactiver des clients assurés via l'API. Les données clients sont accessibles en liste paginée ou en détail par identifiant.

**Why this priority**: Le CRUD clients est le socle de toutes les autres fonctionnalités — les contrats, sinistres et prédictions référencent un client existant.

**Independent Test**: Peut être testé en isolation avec curl ou Swagger — créer un client, le récupérer, le modifier, le désactiver (soft delete), vérifier qu'il n'apparaît plus dans la liste active.

**Acceptance Scenarios**:

1. **Given** une requête de création avec âge, sexe, IMC, enfants, statut fumeur et région, **When** l'API reçoit la requête, **Then** le client est créé et son identifiant est retourné avec statut 201.
2. **Given** un client existant, **When** une requête de détail est envoyée avec son identifiant, **Then** les données complètes du client sont retournées.
3. **Given** un client actif, **When** une requête de suppression est envoyée, **Then** le client est marqué inactif (soft delete) et n'apparaît plus dans la liste active.
4. **Given** un identifiant inexistant, **When** une requête de détail est envoyée, **Then** l'API retourne une erreur 404.

---

### User Story 2 — Prédiction ML et scoring d'assurance (Priority: P2)

Un utilisateur soumet les caractéristiques d'un assuré (âge, sexe, IMC, etc.) et obtient le coût médical prédit, la catégorie de risque et la prime d'assurance calculée avec une décision d'acceptation ou de refus. Si un client_id est fourni, la prédiction est persistée en base.

**Why this priority**: La prédiction ML est la valeur métier centrale du projet — elle justifie l'existence de l'API depuis la perspective assureur.

**Independent Test**: Peut être testé sans client préexistant — envoyer un vecteur de caractéristiques et vérifier que la réponse contient coût prédit, catégorie de risque, prime et décision.

**Acceptance Scenarios**:

1. **Given** un vecteur de caractéristiques valide, **When** prédiction complète demandée, **Then** la réponse contient cout_predit, categorie_risque, score_risque, prime et decision.
2. **Given** un vecteur valide avec client_id existant, **When** prédiction complète demandée, **Then** la prédiction est persistée dans la table predictions.
3. **Given** un vecteur valide, **When** prédiction coût seul demandée, **Then** seul le coût prédit est retourné.
4. **Given** un vecteur valide, **When** prédiction risque seul demandée, **Then** categorie_risque et score_risque sont retournés.
5. **Given** des données manquantes ou invalides, **When** une prédiction est demandée, **Then** l'API retourne une erreur 422 avec les champs concernés.

---

### User Story 3 — Gestion contrats et sinistres (Priority: P3)

Un gestionnaire peut créer des contrats d'assurance pour des clients actifs, modifier leur statut, et enregistrer des sinistres rattachés à des contrats actifs. La création d'un sinistre sur un contrat non actif est refusée.

**Why this priority**: Les contrats et sinistres enrichissent le modèle de données pour les requêtes analytiques et le dashboard, mais ne sont pas bloquants pour le scoring ML.

**Independent Test**: Créer un contrat pour un client existant, puis créer un sinistre rattaché à ce contrat. Tenter de créer un sinistre sur un contrat clôturé et vérifier le rejet 400.

**Acceptance Scenarios**:

1. **Given** un client actif, **When** création d'un contrat avec prime et type de couverture, **Then** le contrat est créé avec statut actif.
2. **Given** un contrat actif, **When** création d'un sinistre avec date, montant et type, **Then** le sinistre est créé avec statut en_cours.
3. **Given** un contrat clôturé ou inexistant, **When** création d'un sinistre, **Then** l'API retourne 400 avec un message explicatif.
4. **Given** un sinistre existant, **When** mise à jour du statut, **Then** le statut est modifié et la réponse reflète le nouvel état.

---

### User Story 4 — Consultation données ETL et KPIs (Priority: P4)

Un utilisateur peut consulter les articles d'actualité et les données météo collectés par le pipeline ETL, et accéder à un tableau de bord de KPIs agrégés sur l'ensemble du portefeuille.

**Why this priority**: Fonctionnalité de consultation en lecture seule, sans impact sur le cœur métier. Nécessaire pour le module Actualités du Streamlit.

**Independent Test**: Appeler les endpoints articles, météo et KPIs et vérifier que des données sont retournées avec la bonne structure.

**Acceptance Scenarios**:

1. **Given** des articles en base, **When** consultation avec filtre par source, **Then** seuls les articles de cette source sont retournés.
2. **Given** des données météo en base, **When** consultation avec filtres région et saison, **Then** les données filtrées sont retournées.
3. **Given** des clients et contrats en base, **When** consultation des KPIs, **Then** la réponse contient nb_clients_actifs, nb_contrats_actifs, sinistres_en_cours, repartition_risque, cout_moyen_predit.

---

### Edge Cases

- Que se passe-t-il si les modèles ML sont absents au démarrage de l'API ?
- Comment l'API réagit-elle si la base de données est inaccessible lors d'une requête ?
- Que retourne la prédiction complète si client_id est fourni mais inexistant ?
- Que se passe-t-il si IMC ou âge est hors des plages vues à l'entraînement ?
- Que retourne GET /stats/kpis si aucun contrat ou aucune prédiction n'existe encore ?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: L'API DOIT exposer un endpoint CRUD complet pour les clients (liste paginée, détail, création, modification, suppression logique).
- **FR-002**: L'API DOIT exposer trois endpoints de prédiction ML distincts : coût seul, risque seul, prédiction complète avec scoring business.
- **FR-003**: L'API DOIT charger les modèles ML une seule fois au démarrage et les réutiliser pour toutes les requêtes.
- **FR-004**: La prédiction complète DOIT persister le résultat en base si un client_id valide est fourni.
- **FR-005**: La création d'un sinistre DOIT vérifier que le contrat associé est actif et retourner 400 avec message explicatif sinon.
- **FR-006**: Les endpoints articles et météo DOIVENT supporter le filtrage par paramètres de requête (source, région, saison).
- **FR-007**: L'API DOIT activer CORS pour permettre les appels depuis l'application Streamlit (localhost:8501).
- **FR-008**: L'API DOIT exposer une documentation interactive auto-générée et navigable sans configuration supplémentaire.
- **FR-009**: L'API DOIT exposer un endpoint de health check retournant le statut opérationnel de l'API et de la base de données.
- **FR-010**: L'endpoint KPIs DOIT retourner les métriques agrégées du portefeuille calculées en temps réel depuis la base de données.
- **FR-011**: La suppression d'un client DOIT être logique — aucune donnée ne doit être physiquement supprimée.
- **FR-012**: Les schémas de validation DOIVENT rejeter les entrées invalides avec des messages d'erreur identifiant le champ et la contrainte violée.

### Key Entities

- **Client**: Assuré avec âge, sexe, IMC, nombre d'enfants, statut fumeur, région. Suppression logique via date d'inactivation.
- **Prédiction**: Résultat d'un scoring ML — coût prédit, score de risque, catégorie, prime calculée, décision, version du modèle. Rattachée optionnellement à un client.
- **Contrat**: Accord entre l'assureur et un client — type de couverture, prime mensuelle, dates, statut.
- **Sinistre**: Déclaration de dommage rattachée à un contrat actif — date, montant, type, statut de traitement.
- **Article**: Contenu scrappé d'actualité santé ou assurance — titre, URL source unique, résumé complet, date de publication.
- **DonneesMeteo**: Mesure météo par région et saison — température moyenne, humidité, précipitations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Chaque endpoint CRUD répond en moins de 500ms pour les opérations simples sur le portefeuille de 1 338 clients.
- **SC-002**: L'endpoint de prédiction complète répond en moins de 2 secondes (deux inférences ML + calcul prime + écriture en base).
- **SC-003**: 100% des routes documentées sont accessibles et testables via la documentation interactive sans configuration supplémentaire.
- **SC-004**: Les erreurs de validation identifient le champ concerné et la contrainte violée dans un format lisible.
- **SC-005**: L'API démarre sans erreur lorsque les modèles ML et la base de données sont disponibles.
- **SC-006**: Les performances de prédiction restent stables sous appels répétés — pas de dégradation due au rechargement des modèles.

## Assumptions

- Les modèles regression.pkl et classification.pkl sont présents dans ml_models/saved_models/ au démarrage.
- business/scoring.py et business/risk_engine.py existent avec des interfaces stables (fonctions calculer_prime et evaluer_decision).
- La base de données PostgreSQL est accessible avec les credentials du fichier .env.
- Aucune authentification n'est requise pour cette version (API interne, accès local ou réseau privé).
- Les listes retournent au maximum 100 éléments par page par défaut (paramètres skip/limit).
- L'application Streamlit tourne sur localhost:8501 — CORS configuré pour cette origine.
- Les schémas Pydantic pour les requêtes ML utilisent les mêmes noms de champs que ceux vus à l'entraînement des modèles.
