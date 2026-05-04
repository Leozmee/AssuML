# Contract: Endpoints Stats et Health

**Routers** : `api/routers/stats.py`, `api/routers/health.py`

---

## GET /api/stats/kpis

**Description** : Tableau de bord agrégé du portefeuille. Calculé en temps réel depuis PostgreSQL.

**Response 200** :
```json
{
  "nb_clients_actifs": 1338,
  "nb_contrats_actifs": 0,
  "sinistres_en_cours": 0,
  "repartition_risque": {
    "faible": 0,
    "moyen": 0,
    "eleve": 0,
    "critique": 0
  },
  "cout_moyen_predit": null
}
```

**Notes** :
- `cout_moyen_predit` : `null` si aucune prédiction en base
- `repartition_risque` : toutes les catégories présentes même avec count=0

---

## GET /health

**Description** : Health check — vérifie que l'API répond et que la BDD est accessible.

**Response 200** :
```json
{
  "status": "ok",
  "database": "ok",
  "models": "ok"
}
```

**Response 503** si BDD ou modèles inaccessibles :
```json
{
  "status": "degraded",
  "database": "error",
  "models": "ok"
}
```
