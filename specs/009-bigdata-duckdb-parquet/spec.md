# Feature Specification: Big Data — DuckDB + Parquet 5M lignes

**Feature Branch**: `009-bigdata-duckdb-parquet`  
**Created**: 2026-06-01  
**Status**: Draft  
**Input**: User description: "Feature 8 — Big Data : DuckDB + Parquet 5M lignes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Génération du jeu de données synthétique (Priority: P1)

Un data engineer lance le script de génération pour produire un fichier Parquet de 5 millions de lignes synthétiques à partir des distributions statistiques du vrai dataset assurance (1 338 lignes).

**Why this priority**: Sans le fichier Parquet, aucune des analyses Big Data n'est possible. C'est la fondation de toute la feature.

**Independent Test**: Exécuter le script et vérifier que `data/big_data/insurance_big.parquet` est créé avec 5 000 000 de lignes et les 11 colonnes attendues.

**Acceptance Scenarios**:

1. **Given** le fichier `data/small_data/insurance.csv` existe, **When** le script de génération est lancé, **Then** un fichier Parquet est créé en moins de 2 minutes avec exactement 5 000 000 lignes.
2. **Given** le script est lancé deux fois avec la même graine (seed=42), **When** les deux fichiers sont comparés, **Then** ils sont identiques (reproductibilité garantie).
3. **Given** le Parquet est généré, **When** ses colonnes sont listées, **Then** les 11 colonnes exactes sont présentes : `age, sex, bmi, children, smoker, region, charges, charges_log, age_group, bmi_category, risk_score`.
4. **Given** le Parquet est généré, **When** les valeurs de `charges` sont vérifiées, **Then** toutes les valeurs sont comprises entre 1 121 et 63 770 USD.

---

### User Story 2 — Analyse analytique via requêtes Big Data (Priority: P2)

Un analyste métier soumet des requêtes analytiques sur le dataset de 5 millions de lignes pour obtenir des statistiques agrégées (par région, tranche d'âge, profil fumeur, etc.) sans charger l'ensemble des données en mémoire.

**Why this priority**: C'est le cœur métier de la feature — démontrer qu'on peut interroger 5M lignes en quelques secondes sans infrastructure lourde.

**Independent Test**: Instancier `DuckDBAnalytics` et appeler chaque méthode — chacune doit retourner un DataFrame Pandas non vide en moins de 5 secondes.

**Acceptance Scenarios**:

1. **Given** le fichier Parquet existe, **When** `stats_par_region()` est appelé, **Then** un DataFrame avec 4 lignes (une par région) et les métriques count, moyenne, médiane, écart-type, min, max est retourné en moins de 5 secondes.
2. **Given** le fichier Parquet existe, **When** `stats_par_fumeur()` est appelé, **Then** un DataFrame comparant fumeurs vs non-fumeurs (proportion ~20.5% / 79.5%) avec charges moyennes et risk_score moyen est retourné.
3. **Given** le fichier Parquet existe, **When** `top_profils_risque()` est appelé, **Then** exactement 10 combinaisons (age_group, bmi_category, smoker) avec les risk_scores les plus élevés sont retournées.
4. **Given** le fichier Parquet existe, **When** `percentiles_charges()` est appelé, **Then** les 7 percentiles P10, P25, P50, P75, P90, P95, P99 sont retournés.
5. **Given** le fichier Parquet existe, **When** `stats_globales()` est appelé, **Then** un résumé avec count total (5 000 000), charges moyennes, risk_score moyen, âge moyen et répartition fumeurs est retourné.

---

### User Story 3 — Tableau de bord Analytics Streamlit (Priority: P3)

Un utilisateur consulte la page Analytics de l'interface Streamlit et explore les insights du portefeuille sur 5 millions de profils à travers des graphiques interactifs et des métriques clés.

**Why this priority**: La visualisation donne de la valeur opérationnelle aux analyses Big Data, mais les stories P1 et P2 doivent être fonctionnelles en premier.

**Independent Test**: Ouvrir la page Analytics dans Streamlit — les métriques globales et les 6 sections de graphiques s'affichent sans erreur, même si l'API FastAPI est démarrée séparément.

**Acceptance Scenarios**:

1. **Given** la page Analytics est ouverte, **When** la page charge, **Then** 4 à 5 métriques globales (total lignes, charges moyennes, risk_score moyen, âge moyen, % fumeurs) s'affichent en haut de page.
2. **Given** la page Analytics est ouverte, **When** l'utilisateur consulte la section "Analyse par région", **Then** un graphique interactif (charges moyennes par région) et un tableau détaillé sont visibles.
3. **Given** la page Analytics est ouverte, **When** l'utilisateur consulte la section "Impact du tabac", **Then** un graphique comparant fumeurs/non-fumeurs pour les charges et le risk_score est visible.
4. **Given** la page Analytics est ouverte, **When** l'utilisateur consulte la section "Distribution des charges", **Then** un histogramme avec bins de 5 000 USD est visible.
5. **Given** la page Analytics est ouverte, **When** l'utilisateur consulte la section "Profils à risque", **Then** un tableau des 10 combinaisons les plus risquées est visible.
6. **Given** la page Analytics est ouverte, **When** la page est consultée en bas, **Then** un footer "5 000 000 lignes analysées via DuckDB" est visible.
7. **Given** le fichier Parquet est absent, **When** la page Analytics est ouverte, **Then** un message d'erreur clair (pas de crash) invite à lancer le script de génération.

---

### Edge Cases

- Que se passe-t-il si `data/big_data/insurance_big.parquet` est absent au démarrage de Streamlit ? → Message d'erreur explicite, pas de crash.
- Que se passe-t-il si le script de génération est interrompu en cours d'exécution ? → Fichier Parquet partiel ou absent ; le script doit être relancé depuis le début.
- Que se passe-t-il si DuckDB n'est pas installé ? → ImportError capturé avec message clair.
- Que se passe-t-il si les valeurs de charges générées sortent des bornes avant clipping ? → Le clipping garantit [1 121, 63 770] sans erreur.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le système DOIT générer 5 000 000 de lignes synthétiques d'assurance à partir des distributions statistiques du fichier source CSV de 1 338 lignes.
- **FR-002**: Les données générées DOIVENT être reproductibles : deux exécutions avec la même graine produisent des résultats identiques.
- **FR-003**: La colonne `charges` DOIT être corrélée aux autres features via une formule linéaire calibrée sur le vrai dataset (non aléatoire pur).
- **FR-004**: Le fichier de sortie DOIT contenir exactement 11 colonnes : `age, sex, bmi, children, smoker, region, charges, charges_log, age_group, bmi_category, risk_score`.
- **FR-005**: La génération DOIT se terminer en moins de 2 minutes sur une machine standard.
- **FR-006**: Le module analytique DOIT fournir 9 méthodes de requêtes retournant des DataFrames Pandas.
- **FR-007**: Chaque requête analytique DOIT s'exécuter en moins de 5 secondes sur 5 millions de lignes.
- **FR-008**: Le module analytique DOIT lire le Parquet en lecture directe sans copie en base de données relationnelle.
- **FR-009**: La page Analytics Streamlit DOIT afficher les 6 sections de visualisation alimentées par lecture directe du Parquet (pas par l'API FastAPI).
- **FR-010**: La page Analytics DOIT afficher un message d'erreur gracieux si le fichier Parquet est absent.
- **FR-011**: Le script de génération DOIT créer automatiquement le dossier `data/big_data/` s'il n'existe pas.

### Key Entities *(include if feature involves data)*

- **Jeu de données synthétique** : 5 millions de profils assurance fictifs, reproduisant les distributions statistiques réelles (âge, IMC, statut fumeur, région, charges). Stocké en Parquet.
- **Feature engineered** : Colonnes calculées ajoutées au Parquet (`charges_log`, `age_group`, `bmi_category`, `risk_score`) permettant des analyses segmentées sans recalcul à la volée.
- **Agrégat analytique** : Résultat d'une requête sur le Parquet — DataFrame Pandas retourné à la couche de visualisation Streamlit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Le script de génération produit un fichier de 5 000 000 lignes en moins de 2 minutes.
- **SC-002**: Chacune des 9 requêtes analytiques retourne un résultat en moins de 5 secondes sur 5 millions de lignes.
- **SC-003**: La page Analytics Streamlit affiche les 6 sections de visualisation sans erreur au premier chargement.
- **SC-004**: Deux exécutions successives du script avec la même graine produisent des données identiques.
- **SC-005**: 100% des valeurs de `charges` générées sont dans l'intervalle [1 121, 63 770] USD.
- **SC-006**: La corrélation entre statut fumeur et charges dans le dataset synthétique est supérieure à 0.7 (cohérente avec le vrai dataset).
- **SC-007**: La page Analytics affiche un message d'erreur clair en moins de 3 secondes si le fichier de données est absent.

## Assumptions

- Le fichier `data/small_data/insurance.csv` avec 1 338 lignes est présent avant l'exécution du script.
- Un moteur de requêtes analytiques compatible Parquet sera installé dans l'environnement Python du projet.
- La page Analytics Streamlit existante (`2_📊_Analytics.py`) sera intégralement réécrite pour remplacer le placeholder de la Feature 7.
- Les modèles ML NE SONT PAS réentraînés sur le dataset synthétique — le Big Data sert uniquement à l'analyse descriptive.
- Le fichier Parquet NE SERA PAS chargé en base de données relationnelle — la lecture se fait directement sur le fichier.
- Le fichier Parquet (~200-400 MB estimé pour 5M lignes) ne sera pas versionné dans git.
- L'accès direct au fichier Parquet depuis Streamlit est une exception documentée à l'architecture standard Streamlit → FastAPI, justifiée par la nature lecture-seule et la taille des données.
