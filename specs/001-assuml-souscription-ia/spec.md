# Feature Specification: AssuML — Système de Souscription Assurance Santé IA

**Feature Branch**: `001-assuml-souscription-ia`
**Created**: 2026-04-07
**Status**: Draft
**Input**: Système complet de souscription assurance santé avec scoring IA,
CRUD clients/contrats/sinistres, analytics Big Data, actualités, météo et
monitoring — validant 21/21 compétences Simplon en 8 semaines.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Gestion complète d'un client (Priority: P1)

Un agent commercial peut créer un dossier client, le consulter, le modifier
et le supprimer logiquement (sans effacement physique des données) afin de
maintenir un référentiel client conforme aux obligations légales.

**Why this priority**: Le client est l'entité centrale du système. Sans CRUD
client fonctionnel, aucune autre fonctionnalité (scoring, contrat, sinistre)
n'est accessible. C'est le MVP minimal.

**Independent Test**: Un agent crée un client avec tous ses attributs, retrouve
ce client dans la liste, modifie son IMC, puis le supprime. Le client supprimé
n'apparaît plus dans les listes actives mais reste traçable dans les archives.

**Acceptance Scenarios**:

1. **Given** un formulaire client vide, **When** l'agent saisit age=35, sexe=homme,
   IMC=28.5, enfants=2, fumeur=non, région=southwest, **Then** le client est créé
   avec un identifiant unique et une date de création, et apparaît dans la liste
   des clients actifs.
2. **Given** un client existant, **When** l'agent modifie l'IMC de 28.5 à 30.0,
   **Then** la modification est enregistrée et reflétée immédiatement.
3. **Given** un client actif, **When** l'agent déclenche la suppression,
   **Then** le client est marqué supprimé (date_suppression renseignée) et
   disparaît des listes actives, sans effacement physique de ses données.
4. **Given** une liste de clients, **When** l'agent filtre par région ou statut,
   **Then** seuls les clients correspondant au filtre sont affichés.

---

### User Story 2 — Scoring IA et décision de souscription (Priority: P1)

Un agent commercial soumet le profil d'un client au système d'intelligence
artificielle pour obtenir une estimation du coût médical annuel, une catégorie
de risque et une décision de souscription automatique.

**Why this priority**: La valeur différenciante du système est le scoring IA.
C'est la compétence centrale de la certification (C9). Sans scoring, le projet
n'est pas un système IA.

**Independent Test**: Un agent saisit un profil (age=45, sexe=femme, IMC=32,
enfants=1, fumeur=oui, région=northeast), déclenche le scoring, et obtient
immédiatement un coût estimé, une catégorie de risque, une prime mensuelle et
une décision. Le résultat est stocké dans l'historique des prédictions.

**Acceptance Scenarios**:

1. **Given** un profil client complet, **When** l'agent déclenche le scoring,
   **Then** le système retourne : coût médical annuel estimé, catégorie de risque
   parmi {faible, moyen, élevé, critique}, score de risque entre 0 et 1, prime
   mensuelle calculée, et décision parmi {accepter, examiner, refuser}.
2. **Given** une catégorie de risque "faible" ou "moyen", **Then** la décision est "accepter".
3. **Given** une catégorie de risque "élevé", **Then** la décision est "examiner".
4. **Given** une catégorie de risque "critique", **Then** la décision est "refuser".
5. **Given** un scoring réalisé, **When** l'agent consulte l'historique,
   **Then** la prédiction est retrouvable avec la version du modèle et la date.

---

### User Story 3 — Gestion des contrats d'assurance (Priority: P2)

Un agent peut créer un contrat d'assurance pour un client ayant obtenu une
décision favorable, suivre son statut et gérer ses dates de validité.

**Why this priority**: Les contrats représentent la concrétisation commerciale
du scoring et sont le support légal des sinistres.

**Independent Test**: Un agent crée un contrat pour un client accepté, spécifie
le type de couverture et la prime mensuelle, puis consulte la liste des contrats
actifs de ce client.

**Acceptance Scenarios**:

1. **Given** un client avec une décision "accepter", **When** l'agent crée un
   contrat, **Then** le contrat est enregistré avec statut "actif", prime mensuelle,
   type de couverture et date de début.
2. **Given** un contrat actif, **When** l'agent le résilie, **Then** le statut
   passe à "résilié" et une date de fin est enregistrée.
3. **Given** un client, **When** l'agent consulte ses contrats, **Then** tous ses
   contrats (actifs et résiliés) sont listés avec leurs informations complètes.

---

### User Story 4 — Déclaration et suivi des sinistres (Priority: P2)

Un agent peut déclarer un sinistre sur un contrat actif et suivre son statut
de traitement.

**Why this priority**: Les sinistres complètent le cycle de vie assurance et
valident les contraintes relationnelles de la base de données.

**Independent Test**: Un agent déclare un sinistre sur un contrat actif en
précisant type, montant et description. Le sinistre apparaît en statut "en cours".

**Acceptance Scenarios**:

1. **Given** un contrat actif, **When** l'agent déclare un sinistre (type, montant > 0),
   **Then** le sinistre est enregistré avec le statut "en cours" et une date de déclaration.
2. **Given** un sinistre en cours, **When** l'agent le clôture, **Then** le statut
   est mis à jour à "clôturé".
3. **Given** un contrat résilié, **When** l'agent tente de déclarer un sinistre,
   **Then** le système refuse avec un message explicatif.

---

### User Story 5 — Analytics Big Data (Priority: P2)

Un analyste visualise des statistiques et tendances sur 10 millions de profils
via des graphiques interactifs pour piloter la stratégie tarifaire.

**Why this priority**: Valide la compétence Big Data (C2). Fonctionnalité
indépendante du CRUD PostgreSQL.

**Independent Test**: Un analyste ouvre le module Analytics, applique un filtre
"fumeurs", et voit en moins de 5 secondes une distribution des coûts, une
répartition régionale et des corrélations sous forme de graphiques interactifs.

**Acceptance Scenarios**:

1. **Given** le module Analytics ouvert, **When** l'analyste consulte la page,
   **Then** au moins 5 graphiques sont affichés : distribution des coûts,
   répartition régionale, impact tabagisme, corrélation âge/coût, corrélation IMC/coût.
2. **Given** les graphiques affichés, **When** un filtre est appliqué,
   **Then** tous les graphiques se mettent à jour de façon cohérente.
3. **Given** une interrogation sur 10 M lignes, **When** la page se charge,
   **Then** les résultats s'affichent en moins de 5 secondes.

---

### User Story 6 — Consultation des actualités assurance (Priority: P3)

Un agent consulte des articles d'actualité récents sur l'assurance santé,
collectés automatiquement par scraping.

**Why this priority**: Valide la compétence web scraping (C1 source 3).

**Independent Test**: Un agent ouvre le module Actualités et voit une liste
d'articles avec titre, source, date et résumé, datés de moins de 30 jours.

**Acceptance Scenarios**:

1. **Given** le module Actualités ouvert, **When** l'agent consulte la liste,
   **Then** au moins 5 articles sont affichés avec titre, source, URL, résumé
   et date de publication.
2. **Given** un article affiché, **When** l'agent clique sur le lien,
   **Then** il est redirigé vers la source originale.
3. **Given** la source de scraping indisponible, **When** le module se charge,
   **Then** les derniers articles en base sont affichés sans erreur visible.

---

### User Story 7 — Enrichissement météorologique par région (Priority: P3)

Un analyste consulte les données météorologiques moyennes par région pour
enrichir l'analyse des risques régionaux.

**Why this priority**: Valide la compétence API externe (C1 source 2).

**Independent Test**: Un analyste sélectionne la région "southeast" et voit
température moyenne, humidité et précipitations pour les données les plus récentes.

**Acceptance Scenarios**:

1. **Given** le module Météo accessible, **When** l'analyste sélectionne une
   région, **Then** température moyenne, humidité et précipitations sont affichées.
2. **Given** les données météo, **When** l'analyste compare deux régions,
   **Then** les indicateurs des deux régions sont affichés côte à côte.

---

### User Story 8 — Monitoring ML et infrastructure (Priority: P3)

Un data scientist consulte les métriques de performance des modèles ML et les
indicateurs système pour détecter une dégradation.

**Why this priority**: Valide les compétences monitoring et MLOps. Indispensable
pour une mise en production responsable.

**Independent Test**: Un data scientist ouvre le module Monitoring et voit les
métriques actuelles de chaque modèle avec un indicateur visuel si les métriques
dégradent par rapport à la baseline.

**Acceptance Scenarios**:

1. **Given** le module Monitoring ouvert, **When** le data scientist consulte
   la section modèles, **Then** les métriques des deux modèles sont affichées
   (R², MAE, RMSE ; accuracy, F1, matrice de confusion) avec comparaison baseline.
2. **Given** une métrique dégradée (ex. R² < 0.70), **Then** un indicateur
   visuel d'alerte est affiché.
3. **Given** le module ouvert, **When** la section infrastructure est consultée,
   **Then** les métriques système (disponibilité, temps de réponse, CPU/mémoire)
   sont accessibles.

---

### Edge Cases

- Un client sans email ni téléphone DOIT pouvoir être créé (champs optionnels RGPD).
- Un profil avec IMC hors plage [10–80] ou age hors plage [18–120] DOIT être
  rejeté avec un message d'erreur explicite avant tout scoring.
- Un scoring sur un profil incomplet DOIT retourner une erreur métier claire.
- Un sinistre avec montant nul ou négatif DOIT être rejeté.
- Le module Analytics DOIT afficher un message d'indisponibilité si le fichier
  Parquet est absent, sans erreur non gérée.
- Un contrat résilié ne peut pas recevoir de nouveaux sinistres.
- Le scraping échoue si la source est indisponible : le système DOIT afficher
  les derniers articles en cache.

---

## Requirements *(mandatory)*

### Functional Requirements

**CRUD Clients**
- **FR-001**: Le système DOIT permettre la création d'un client avec : âge
  (18–120), sexe, IMC (10–80), enfants (0–20), statut fumeur, région parmi
  {southwest, southeast, northwest, northeast}, email (optionnel), téléphone (optionnel).
- **FR-002**: Le système DOIT permettre la recherche et le filtrage des clients
  actifs par région, statut fumeur et catégorie de risque.
- **FR-003**: Le système DOIT permettre la modification de tout attribut d'un client.
- **FR-004**: La suppression DOIT être logique (soft delete via date_suppression),
  sans effacement physique des données.

**Scoring IA**
- **FR-005**: Le système DOIT prédire le coût médical annuel (régression) d'un
  profil client.
- **FR-006**: Le système DOIT classifier le niveau de risque en 4 catégories :
  faible (< 5 000), moyen (5 000–15 000), élevé (15 000–30 000), critique (> 30 000).
- **FR-007**: Le système DOIT calculer automatiquement une décision :
  faible/moyen → accepter, élevé → examiner, critique → refuser.
- **FR-008**: Le système DOIT calculer une prime mensuelle estimée à partir
  du coût prédit.
- **FR-009**: Chaque prédiction DOIT être persistée avec la version du modèle,
  la date et l'ensemble des inputs.

**Contrats**
- **FR-010**: Le système DOIT permettre la création d'un contrat (statut, prime
  mensuelle, type de couverture, date de début, date de fin optionnelle).
- **FR-011**: Le système DOIT permettre la consultation des contrats par client.
- **FR-012**: Le système DOIT permettre la mise à jour du statut d'un contrat.

**Sinistres**
- **FR-013**: Le système DOIT permettre la déclaration d'un sinistre sur un
  contrat actif (type, montant > 0, description, date).
- **FR-014**: Le système DOIT permettre la mise à jour du statut d'un sinistre.
- **FR-015**: Le système DOIT refuser la création d'un sinistre sur un contrat
  non actif.

**Analytics Big Data**
- **FR-016**: Le système DOIT afficher au moins 5 graphiques interactifs sur
  les données Big Data (10 M lignes) : distribution coûts, répartition régionale,
  impact tabagisme, corrélation âge/coût, corrélation IMC/coût.
- **FR-017**: Le module Analytics DOIT permettre le filtrage par région, tranche
  d'âge et statut fumeur.

**Actualités**
- **FR-018**: Le système DOIT afficher les articles collectés (titre, source,
  URL, résumé, date de publication).
- **FR-019**: Le scraping DOIT collecter des articles depuis au moins une source
  publique d'actualité assurance/santé.

**Météo**
- **FR-020**: Le système DOIT collecter et afficher les données météorologiques
  (température moyenne, humidité, précipitations) pour les 4 régions.

**Monitoring**
- **FR-021**: Le système DOIT exposer les métriques des deux modèles ML : R²,
  MAE, RMSE (régression) ; accuracy, F1, matrice de confusion (classification).
- **FR-022**: Le système DOIT signaler visuellement toute métrique dépassant
  les seuils d'alerte configurés.
- **FR-023**: Le système DOIT exposer des métriques infrastructure (disponibilité,
  temps de réponse, charge système).

### Key Entities

- **Client** : âge, sexe, IMC, enfants, fumeur, région (FK), email?, téléphone?,
  date_creation, date_suppression?. Entité centrale.
- **Prédiction** : cout_predit, score_risque, categorie_risque, decision, prime,
  version_modele, date_prediction. Rattachée à un client.
- **Contrat** : statut, prime_mensuelle, type_couverture, date_debut, date_fin?.
  Rattaché à un client.
- **Sinistre** : type_sinistre, montant_sinistre (> 0), statut_sinistre,
  description, date_sinistre. Rattaché à un contrat.
- **Région** : référentiel fixe des 4 zones géographiques US.
- **DonnéesMétéo** : temperature_moy, humidite_moy, precipitations, saison,
  date_collecte. Rattachée à une région.
- **Article** : titre, url_source (unique), nom_source, resume, date_publication,
  date_scraping.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un agent complète la création d'un client et obtient un scoring
  complet en moins de 10 secondes au total.
- **SC-002**: Les graphiques Analytics sur 10 M lignes s'affichent en moins de
  5 secondes après sélection d'un filtre.
- **SC-003**: La régression atteint R² ≥ 0.70 et la classification atteint
  accuracy ≥ 0.80 sur les données de test.
- **SC-004**: 100% des endpoints API répondent correctement lors des tests
  d'intégration (cas nominaux et cas d'erreur).
- **SC-005**: Le système est opérationnel avec un taux de disponibilité ≥ 99%
  pendant la phase de démonstration (soutenance).
- **SC-006**: La suite de tests automatisés couvre les 8 fonctionnalités
  principales et s'exécute sans erreur dans le pipeline CI/CD.
- **SC-007**: Le système valide les 21 compétences du référentiel Simplon,
  attestées lors de la soutenance (fin semaine 8, ~2026-06-01).
- **SC-008**: Zéro violation RGPD : aucun DELETE physique, aucune donnée
  personnelle hardcodée dans le code source.

---

## Assumptions

- Les 4 régions sont fixes et pré-remplies en base. Aucune gestion dynamique
  des régions n'est prévue en v1.
- La prime mensuelle est calculée par une règle métier simple (coût annuel prédit
  / 12 × coefficient de risque). La formule exacte est définie à l'implémentation.
- Le dataset Kaggle `insurance.csv` (1 338 lignes) est suffisant pour entraîner
  et valider les modèles dans le cadre de la certification.
- Le Big Data (10 M lignes Parquet) est généré synthétiquement à partir du
  dataset Kaggle.
- L'authentification utilisateur est hors périmètre v1 (environnement contrôlé
  de certification, usage interne).
- Le scraping cible des sources publiques francophones ou anglophones d'actualité
  assurance/santé. La liste exacte des sources est définie à l'implémentation.
- Les seuils d'alerte monitoring (ex. R² < 0.70) sont configurables sans
  modification de la présente spec.
- L'API OpenWeatherMap est utilisée avec la clé gratuite (un appel par région
  par jour maximum).
- Le développement est réalisé par un seul développeur (Leo) en 8 semaines,
  avec environnement local Docker et GitHub Actions pour la CI/CD.
