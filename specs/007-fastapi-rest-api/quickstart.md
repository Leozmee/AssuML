# Quickstart: API REST FastAPI complète

**Feature**: 007-fastapi-rest-api | **Date**: 2026-05-04

## Démarrage rapide

```bash
# Depuis la racine du projet
uvicorn api.main:app --reload --port 8000

# Documentation interactive
open http://localhost:8000/docs
```

## Scénario 1 : CRUD client complet (US1)

```bash
# 1. Créer un client
curl -X POST http://localhost:8000/api/clients \
  -H "Content-Type: application/json" \
  -d '{"age": 35, "sexe": "femme", "imc": 24.0, "enfants": 1, "fumeur": false, "region_id": 2}'

# → {"client_id": 1339, "age": 35, "sexe": "femme", ...}

# 2. Récupérer le client
curl http://localhost:8000/api/clients/1339

# 3. Modifier l'IMC
curl -X PUT http://localhost:8000/api/clients/1339 \
  -H "Content-Type: application/json" \
  -d '{"imc": 26.5}'

# 4. Soft delete
curl -X DELETE http://localhost:8000/api/clients/1339
# → {"message": "Client désactivé", "client_id": 1339}

# 5. Vérifier qu'il n'apparaît plus dans la liste
curl "http://localhost:8000/api/clients?limit=5"
```

## Scénario 2 : Prédiction ML complète (US2)

```bash
# Prédiction anonyme (sans persistance)
curl -X POST http://localhost:8000/api/predict/complet \
  -H "Content-Type: application/json" \
  -d '{"age": 45, "sexe": 1, "imc": 32.5, "enfants": 2, "fumeur": 1, "region": "southeast"}'

# → {"cout_predit": 28543.67, "categorie_risque": "eleve", "score_risque": 0.81,
#    "prime": 38533.95, "decision": "examiner", "prediction_id": null}

# Prédiction avec persistance (client existant)
curl -X POST http://localhost:8000/api/predict/complet \
  -H "Content-Type: application/json" \
  -d '{"age": 45, "sexe": 1, "imc": 32.5, "enfants": 2, "fumeur": 1, "region": "southeast", "client_id": 1}'

# → même réponse mais prediction_id non null → vérifiable dans /api/stats/kpis
```

## Scénario 3 : Contrat + sinistre (US3)

```bash
# 1. Créer un contrat
curl -X POST http://localhost:8000/api/contrats \
  -H "Content-Type: application/json" \
  -d '{"client_id": 1, "prime_mensuelle": 250.0, "date_debut": "2026-05-01", "type_couverture": "base"}'

# → {"contrat_id": 1, "statut": "actif", ...}

# 2. Créer un sinistre sur contrat actif
curl -X POST http://localhost:8000/api/sinistres \
  -H "Content-Type: application/json" \
  -d '{"contrat_id": 1, "date_sinistre": "2026-05-10", "montant_sinistre": 1200.0, "type_sinistre": "hospitalisation"}'

# → {"sinistre_id": 1, "statut_sinistre": "en_cours", ...}

# 3. Clôturer le contrat
curl -X PUT http://localhost:8000/api/contrats/1/statut \
  -H "Content-Type: application/json" \
  -d '{"statut": "cloture"}'

# 4. Tenter un sinistre sur contrat clôturé → 400
curl -X POST http://localhost:8000/api/sinistres \
  -H "Content-Type: application/json" \
  -d '{"contrat_id": 1, "date_sinistre": "2026-05-15", "montant_sinistre": 500.0, "type_sinistre": "consultation"}'
# → HTTP 400 {"detail": "Le contrat 1 n'est pas actif (statut: cloture)"}
```

## Scénario 4 : Données ETL et KPIs (US4)

```bash
# Articles filtrés par source
curl "http://localhost:8000/api/articles?source=santemagazine.fr"
# → [{"article_id": 1, "titre": "...", "nom_source": "santemagazine.fr", ...}]

# Météo filtrée
curl "http://localhost:8000/api/meteo?region=southeast&saison=printemps"

# KPIs du portefeuille
curl http://localhost:8000/api/stats/kpis
# → {"nb_clients_actifs": 1338, "nb_contrats_actifs": 1, "sinistres_en_cours": 1, ...}

# Health check
curl http://localhost:8000/health
# → {"status": "ok", "database": "ok", "models": "ok"}
```

## Validation avec pytest

```bash
# Tests contract API (nécessite l'API en cours d'exécution)
pytest tests/contract/ -v

# Tests unitaires schemas Pydantic (pas de BDD requise)
pytest tests/unit/test_schemas.py -v
```

## Variables d'environnement requises

```bash
# .env
DATABASE_URL=postgresql://assuml_user:password@localhost:5432/assuml_db
# Les modèles .pkl doivent être dans ml_models/saved_models/
```
