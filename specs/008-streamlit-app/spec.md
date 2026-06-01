# Feature Specification: AssuML — Interface Streamlit

**Feature Branch**: `008-streamlit-app`
**Created**: 2026-06-01
**Status**: In Progress
**Input**: Application Streamlit complète consommant l'API FastAPI (007) pour exposer
scoring IA, gestion clients/contrats/sinistres, analytics Big Data et monitoring ML.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Scoring IA (Priority: P1)

Un agent commercial saisit un profil assuré (âge, sexe, IMC, enfants, fumeur, région)
et obtient en un clic le coût médical prédit, la catégorie de risque, la prime
mensuelle et la décision de souscription, avec des jauges visuelles colorées.

**Independent Test**: Saisir age=45, sexe=Homme, IMC=28.5, enfants=2, fumeur=Non,
région=Northeast → cliquer "Scoring complet" → affichage des 3 jauges + décision
colorée (vert/orange/rouge).

**Acceptance Scenarios**:
1. **Given** le formulaire de scoring, **When** l'agent clique "Scoring complet",
   **Then** trois jauges Plotly (coût, risque, prime) s'affichent avec la décision
   colorée.
2. **Given** un client_id valide, **When** l'agent score avec ce client_id,
   **Then** la prédiction est persistée en base et l'ID affiché.
3. **Given** l'API indisponible, **When** l'agent clique "Scorer",
   **Then** un message d'erreur clair s'affiche (pas de crash).

---

### User Story 2 — Gestion CRUD (Priority: P1)

Un agent voit la liste de tous les clients avec leur statut de contrat en temps réel,
peut créer/modifier/supprimer des clients, créer des contrats et déclarer des sinistres
avec les règles métier enforced côté UI.

**Independent Test**: Créer un client → vérifier qu'il apparaît dans le tableau →
créer un contrat → vérifier badge "Actif" → déclarer un sinistre → vérifier dans la
sous-section sinistres → suspendre le contrat → vérifier que "+ Sinistre" devient
"Sinistre bloqué".

**Acceptance Scenarios**:
1. **Given** un client sans contrat, **Then** la colonne "Statut contrat" affiche
   "⚫ Aucun", bouton "+ Contrat" actif, "⛔ Sinistre" grisé.
2. **Given** un client avec contrat actif, **Then** badge "🟢 Actif", contrat grisé
   "Contrat existant", bouton "+ Sinistre" actif.
3. **Given** un client avec contrat suspendu, **Then** badge "🟠 Suspendu",
   "🔒 Bloqué" grisé.
4. **Given** un soft delete, **Then** confirmation requise avant suppression,
   le client disparaît de la liste.

---

### User Story 3 — Analytics (Priority: P2)

Un manager voit les 5 KPIs globaux du portefeuille et comprend que la partie
Big Data sera disponible après la Feature 8.

**Independent Test**: Ouvrir la page Analytics → 5 métriques s'affichent en haut
(nb_clients_actifs, nb_contrats_actifs, sinistres_en_cours, cout_moyen_predit,
total_predictions) → placeholder Big Data visible.

---

### User Story 4 — Monitoring (Priority: P3)

Un data scientist voit la santé de l'API, les métriques ML de production (R², accuracy,
MAE, F1) et des graphiques de drift simulé sur 12 semaines.

**Independent Test**: Ouvrir Monitoring → badges API/BDD/ML en vert → métriques
R²=0.8533, Accuracy=0.8918 affichées → graphiques drift sur 12 semaines visibles.

---

### User Story 5 — Actualités (Priority: P4)

Un agent voit les articles scrappés par l'ETL, filtrés par source, avec résumé
et lien, et consulte les données météo par région et saison.

**Independent Test**: Ouvrir Actualités → sélectionner une source → articles dans
des st.expander() → filtrer météo par région=northeast → tableau affiché.

---

## Scope

**In Scope**:
- Application Streamlit 5 pages + point d'entrée app.py
- Client HTTP centralisé (utils/api_client.py) avec gestion d'erreurs
- Composants réutilisables (charts, forms, metrics, tables)
- Toutes les règles métier du CRUD enforced côté UI
- Graphiques Plotly pour scoring, monitoring et météo

**Out of Scope**:
- Intégration DuckDB / Big Data (Feature 8)
- Authentification / sessions utilisateur
- Déploiement Docker Streamlit (Feature 9)
- Tests automatisés Streamlit (selenium/playwright)

---

## Technical Requirements

- **Streamlit** 1.32+ avec `st.set_page_config(layout="wide")`
- **Plotly** pour tous les graphiques (jauges, barres, scatter)
- **Requests** pour appels HTTP vers FastAPI localhost:8000
- **Pandas** pour la manipulation des tableaux
- Architecture multipage native Streamlit (`pages/` directory)
- Timeout 10s sur tous les appels API
- Cache `@st.cache_data(ttl=30)` sur les listes clients et contrats
- Pagination 20 clients par page dans le CRUD

---

## Non-functional Requirements

- Chargement page < 3s sur 1 338 clients (avec cache)
- Messages d'erreur clairs si API indisponible (pas de crash)
- Pas de credentials hardcodés
- Compatible Python 3.11
