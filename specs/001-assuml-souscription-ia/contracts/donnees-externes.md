# Contrat API : Données Externes (Météo & Articles)

**Base URL**: `http://localhost:8000/api`
**Format**: JSON — Content-Type: application/json

---

## GET /api/meteo

**Description**: Données météorologiques par région (dernière collecte disponible).

**Query parameters** :
| Paramètre | Type | Optionnel | Description |
|-----------|------|-----------|-------------|
| `region` | string | oui | Filtrer par région |
| `saison` | string | oui | Filtrer par saison |

**Response 200**:
```json
{
  "donnees": [
    {
      "meteo_id": 1,
      "region": "southwest",
      "temperature_moy": 22.5,
      "humidite_moy": 35.0,
      "precipitations": 12.3,
      "saison": "printemps",
      "date_collecte": "2026-04-07T08:00:00"
    },
    {
      "meteo_id": 2,
      "region": "southeast",
      "temperature_moy": 26.1,
      "humidite_moy": 68.0,
      "precipitations": 45.7,
      "saison": "printemps",
      "date_collecte": "2026-04-07T08:00:00"
    }
  ]
}
```

---

## GET /api/articles

**Description**: Articles d'actualité assurance/santé collectés par scraping.

**Query parameters** :
| Paramètre | Type | Optionnel | Description |
|-----------|------|-----------|-------------|
| `nom_source` | string | oui | Filtrer par source |
| `depuis` | date | oui | Articles publiés après cette date (ISO) |
| `limit` | int | oui | Défaut: 20 |
| `offset` | int | oui | Défaut: 0 |

**Response 200**:
```json
{
  "total": 8,
  "articles": [
    {
      "article_id": 1,
      "titre": "Les nouvelles tendances de l'assurance santé en 2026",
      "url_source": "https://exemple.fr/article-1",
      "nom_source": "MoneyVox",
      "resume": "Analyse des évolutions tarifaires...",
      "date_publication": "2026-04-05",
      "date_scraping": "2026-04-07T06:00:00"
    }
  ]
}
```

---

## Contrats Internes (non exposés via API REST)

### DuckDB — Module Analytics Streamlit (accès direct)

Le module `2_analytics.py` interroge DuckDB directement sur le fichier Parquet.
Les requêtes types utilisées :

```sql
-- Distribution des coûts médicaux
SELECT
  CASE
    WHEN charges < 5000  THEN 'faible'
    WHEN charges < 15000 THEN 'moyen'
    WHEN charges < 30000 THEN 'eleve'
    ELSE 'critique'
  END AS categorie,
  COUNT(*) AS nb_clients,
  AVG(charges) AS cout_moyen
FROM read_parquet('data/big_data/insurance_big.parquet')
WHERE smoker = :smoker_filter   -- paramètre Streamlit
GROUP BY categorie;

-- Répartition régionale
SELECT region, COUNT(*) AS nb, AVG(charges) AS cout_moyen
FROM read_parquet('data/big_data/insurance_big.parquet')
GROUP BY region;

-- Corrélation âge / charges par région
SELECT age_group, region, AVG(charges) AS cout_moyen
FROM read_parquet('data/big_data/insurance_big.parquet')
GROUP BY age_group, region
ORDER BY age_group;
```

**Paramètres de filtrage** : `region` (string), `smoker` (string 'yes'/'no'),
`age_group` (string) — exposés via widgets Streamlit (`st.selectbox`, `st.multiselect`).

---

## Prometheus — Endpoint métriques (interne)

**URL**: `http://localhost:8000/metrics`
**Format**: texte Prometheus (scraping par Prometheus toutes les 15 s)

**Métriques exposées** :
```
# HELP http_requests_total Nombre total de requêtes HTTP
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/api/predict/complet",status="200"} 42

# HELP http_request_duration_seconds Durée des requêtes
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 38
http_request_duration_seconds_bucket{le="0.5"} 42

# HELP ml_predictions_total Prédictions par catégorie de risque
# TYPE ml_predictions_total counter
ml_predictions_total{categorie="faible"} 15
ml_predictions_total{categorie="moyen"} 18
ml_predictions_total{categorie="eleve"} 7
ml_predictions_total{categorie="critique"} 2

# HELP ml_model_r2_score R² du modèle de régression
# TYPE ml_model_r2_score gauge
ml_model_r2_score{modele="regression"} 0.827
```
