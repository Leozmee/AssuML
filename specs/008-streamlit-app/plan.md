# Plan d'implémentation: AssuML — Interface Streamlit

**Feature Branch**: `008-streamlit-app`
**Effort estimé**: 2–3 jours
**Dépendances**: 007-fastapi-rest-api ✅ (API complète, 7 routers, 29/29 tasks)

---

## Architecture retenue

```
streamlit_app/
├── app.py                    # Point d'entrée, config globale
├── pages/
│   ├── 1_🎯_Scoring.py      # Scoring ML (3 endpoints predict)
│   ├── 2_📊_Analytics.py    # KPIs + placeholder Big Data
│   ├── 3_👥_CRUD.py         # Clients/Contrats/Sinistres
│   ├── 4_📈_Monitoring.py   # Santé API + métriques ML + drift
│   └── 5_📰_Actualites.py   # Articles + météo
├── components/
│   ├── charts.py             # Jauges Plotly, graphiques ML
│   ├── forms.py              # Formulaires st.form réutilisables
│   ├── metrics.py            # KPI display, badges, décision
│   └── tables.py             # DataFrames Pandas formatés
└── utils/
    └── api_client.py         # Client HTTP centralisé (requests)
```

## Décisions d'architecture

### Client HTTP
- Fonctions nommées par ressource (pas de classe) pour rester testables isolément
- Retour `(data, error)` — les pages affichent `st.error(error)` si besoin
- `get_all_clients()` / `get_all_contrats()` : loop de pagination auto (limit=100)

### CRUD — gestion des actions par ligne
- Contrats indexés par `client_id` en mémoire (1 seul appel GET /contrats global)
- Session state `client_action` + `selected_client` pour les actions modales
- Pagination 20 lignes/page pour les 1 338 clients
- `@st.cache_data(ttl=30)` — invalider manuellement après chaque mutation

### Scoring
- Conversion sexe/fumeur str→int dans la page (pas dans api_client)
- 3 boutons dans le même `st.form()` → `form_submit_button` différenciés
- Jauges Plotly `go.Indicator(mode="gauge+number")` côte à côte

### Monitoring
- Lecture directe de `ml_models/saved_models/metadata.json` (fichier local)
- Drift simulé avec numpy (valeurs décroissantes + bruit gaussien sur 12 semaines)
- Seuils d'alerte hardcodés : R²<0.80, Accuracy<0.85

### Analytics
- Placeholder Big Data `st.info()` avec code snippet DuckDB
- KPIs + graphique répartition risque si données disponibles

### Actualités
- Extraction des sources disponibles au premier chargement
- Articles dans `st.expander(titre)` avec résumé + lien
- Météo dans `st.dataframe()` + scatter Plotly

---

## Flux de données

```
Streamlit → requests → FastAPI :8000 → PostgreSQL
                   ↘ ml_models/prediction/predict.py (ML singleton)
Monitoring → metadata.json (lecture locale)
Analytics (Feature 8) → DuckDB → insurance_big.parquet
```

---

## Contraintes techniques

- Streamlit 1.32+ (pas de `@st.dialog` — utiliser session state pour les modaux)
- Emoji dans les noms de fichiers pages/ (support natif Streamlit multipage)
- Le CRUD charge tous les clients (1 338) + tous les contrats en mémoire avec cache
- `import sys; sys.path.insert(0, ...)` dans chaque page pour résoudre les imports
