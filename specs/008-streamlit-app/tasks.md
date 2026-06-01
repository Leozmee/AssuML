# Tasks: Interface Streamlit AssuML

**Input**: Design documents from `/specs/008-streamlit-app/`
**Prerequisites**: plan.md ✅, spec.md ✅
**Dépendance**: 007-fastapi-rest-api ✅ (toutes les routes API disponibles)

**Organisation**: 9 tâches séquentielles — infrastructure → composants → pages.

---

## Tâche 1 — utils/api_client.py

**Objectif**: Client HTTP centralisé pour tous les appels vers FastAPI.

- [X] T001 Créer `streamlit_app/utils/__init__.py` et `streamlit_app/utils/api_client.py`
- [X] T002 Implémenter les fonctions `_get`, `_post`, `_put`, `_delete` avec gestion d'erreurs (tuple `(data, error)`)
- [X] T003 Implémenter `get_health()`, `get_kpis()`
- [X] T004 Implémenter `get_clients()`, `get_all_clients()`, `get_client(id)`, `create_client()`, `update_client()`, `delete_client()`
- [X] T005 Implémenter `predict_cout()`, `predict_risque()`, `predict_complet()`
- [X] T006 Implémenter `get_contrats()`, `get_all_contrats()`, `create_contrat()`, `update_contrat_statut()`
- [X] T007 Implémenter `get_sinistres()`, `get_all_sinistres()`, `create_sinistre()`, `update_sinistre_statut()`
- [X] T008 Implémenter `get_articles()`, `get_meteo()`

**Checkpoint**: Appel `api.get_health()` retourne `("ok", None)` avec l'API active. ✅

---

## Tâche 2 — components/

**Objectif**: Composants réutilisables pour graphiques, formulaires, métriques, tableaux.

- [X] T009 Créer `streamlit_app/components/__init__.py`
- [X] T010 Créer `components/charts.py` : `jauge_cout()`, `jauge_risque()`, `jauge_prime()`, `graphique_repartition_risque()`, `graphique_metriques_ml()`
- [X] T011 Créer `components/metrics.py` : `afficher_kpis()`, `badge_decision()`, `badge_statut_contrat()`, `afficher_metriques_modele()`
- [X] T012 Créer `components/forms.py` : `form_predict()`, `form_nouveau_client()`, `form_modifier_client()`, `form_nouveau_contrat()`, `form_nouveau_sinistre()`
- [X] T013 Créer `components/tables.py` : `df_clients()`, `df_contrats()`, `df_sinistres()`, `df_articles()`, `df_meteo()`

**Checkpoint**: Les composants importent sans erreur dans un shell Python. ✅

---

## Tâche 3 — app.py

**Objectif**: Point d'entrée avec config globale et page d'accueil.

- [X] T014 Créer `streamlit_app/app.py` avec `st.set_page_config(layout="wide")`, titre, tableau de navigation, message d'info API

**Checkpoint**: `streamlit run streamlit_app/app.py` démarre sans erreur, page d'accueil visible. ✅

---

## Tâche 4 — pages/1_🎯_Scoring.py

**Objectif**: Formulaire scoring complet avec jauges et décision colorée.

- [X] T015 Créer le formulaire avec les 6 champs + client_id optionnel dans `st.form`
- [X] T016 Implémenter les 3 boutons (`Scoring complet`, `Coût seul`, `Risque seul`) différenciés
- [X] T017 Afficher les 3 jauges Plotly côte à côte après scoring complet
- [X] T018 Afficher le badge décision coloré (vert/orange/rouge) avec `badge_decision()`

**Checkpoint**: Saisir un profil → cliquer "Scoring complet" → 3 jauges + décision s'affichent. ✅

---

## Tâche 5 — pages/3_👥_CRUD.py

**Objectif**: Tableau clients paginé avec actions context-aware par ligne.

- [X] T019 Charger tous les clients + contrats avec `@st.cache_data(ttl=30)` et pagination
- [X] T020 Afficher le tableau avec colonnes ID, Âge, Sexe, IMC, Fumeur, Région, Statut contrat, Actions
- [X] T021 Implémenter les badges de statut contrat via `badge_statut_contrat()`
- [X] T022 Implémenter les boutons d'action avec règles métier :
  - Pas de contrat → "+ Contrat" actif, "⛔ Sinistre" grisé
  - Contrat actif → contrat grisé barré, "+ Sinistre" actif
  - Contrat suspendu → contrat grisé, "🔒 Bloqué" grisé
- [X] T023 Implémenter le panneau d'action (session state) pour Voir/Modifier/Supprimer/+Contrat/+Sinistre
- [X] T024 Implémenter le soft delete avec message de confirmation `st.warning()`
- [X] T025 Ajouter les sous-sections Contrats et Sinistres dans `st.expander()`

**Checkpoint**: Créer un client → badge "Aucun" → créer contrat → badge "Actif" → "+ Sinistre" disponible. ✅

---

## Tâche 6 — pages/4_📈_Monitoring.py

**Objectif**: Tableau de bord de santé système et métriques ML.

- [X] T026 Appeler `get_health()` et afficher 3 badges (API, BDD, Modèles ML)
- [X] T027 Lire `ml_models/saved_models/metadata.json` et afficher métriques via `afficher_metriques_modele()`
- [X] T028 Générer graphiques de drift simulé (R², accuracy, MAE sur 12 semaines) avec seuils d'alerte
- [X] T029 Afficher KPIs via `afficher_kpis()`

**Checkpoint**: Ouvrir Monitoring → 3 badges API/BDD/ML en vert → R²=0.8533, Accuracy=0.8918 affichés. ✅

---

## Tâche 7 — pages/5_📰_Actualites.py

**Objectif**: Articles scrappés et données météo avec filtres.

- [X] T030 Afficher les articles dans `st.expander()` avec filtre source dynamique
- [X] T031 Afficher les données météo dans `st.dataframe()` avec filtres région + saison
- [X] T032 Ajouter scatter Plotly Température vs Précipitations si données disponibles

**Checkpoint**: Page s'affiche sans erreur si articles/météo vides (message informatif). ✅

---

## Tâche 8 — pages/2_📊_Analytics.py

**Objectif**: KPIs globaux + placeholder Big Data.

- [X] T033 Afficher les 5 KPIs via `afficher_kpis()` + graphique répartition risque
- [X] T034 Afficher placeholder Big Data avec `st.info()` + code snippet DuckDB

**Checkpoint**: KPIs s'affichent, répartition risque en barres, placeholder visible. ✅

---

## Tâche 9 — Tests manuels

**Objectif**: Vérification bout-en-bout du flux complet.

- [ ] T035 Lancer `uvicorn api.main:app --reload --port 8000` puis `streamlit run streamlit_app/app.py`
- [ ] T036 Vérifier chaque page : Scoring, Analytics, CRUD, Monitoring, Actualités
- [ ] T037 Tester le flux complet : créer client → scorer → créer contrat → créer sinistre
- [ ] T038 Vérifier les états grisés du CRUD (contrat existant, sinistre bloqué)
- [ ] T039 Tester le message d'erreur quand l'API est stoppée

---

## Dépendances

```
T001–T008 séquentiels (api_client)
T009–T013 parallèles (composants)
T014 après T001
T015–T018 après T009–T013 et T014 (Scoring)
T019–T025 après T009–T013 et T014 (CRUD)
T026–T029 après T009–T013 et T014 (Monitoring)
T030–T032 après T009–T013 et T014 (Actualités)
T033–T034 après T009–T013 et T014 (Analytics)
T035–T039 après toutes les implémentations
```
