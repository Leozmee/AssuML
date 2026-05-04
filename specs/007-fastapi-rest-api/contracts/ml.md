# Contract: Endpoints ML

**Router** : `api/routers/ml.py` | **Prefix** : `/api`

---

## Corps de requête commun : PredictRequest

```json
{
  "age": 45,
  "sexe": 1,
  "imc": 32.5,
  "enfants": 2,
  "fumeur": 1,
  "region": "southeast",
  "client_id": null
}
```

**Validation Pydantic** :
- `age` : int, 18 ≤ age ≤ 120
- `sexe` : int, 0 (homme) ou 1 (femme)
- `imc` : float, 10.0 ≤ imc ≤ 80.0
- `enfants` : int, 0 ≤ enfants ≤ 10
- `fumeur` : int, 0 ou 1
- `region` : Literal["northeast", "northwest", "southeast", "southwest"]
- `client_id` : int?, optionnel (uniquement pour /predict/complet)

---

## POST /api/predict/cout

**Description** : Prédit uniquement le coût médical annuel.

**Response 200** :
```json
{
  "cout_predit": 12543.67
}
```

---

## POST /api/predict/risque

**Description** : Prédit la catégorie de risque et le score de confiance.

**Response 200** :
```json
{
  "categorie_risque": "moyen",
  "score_risque": 0.74
}
```

---

## POST /api/predict/complet

**Description** : Orchestre les deux modèles + logique métier. Persiste en base si `client_id` valide fourni.

**Orchestration** :
1. `predict_cost(features)` → `cout_predit`
2. `predict_risk(features)` → `(categorie_risque, score_risque)`
3. `calculer_prime(cout_predit, categorie_risque)` → `prime`
4. `get_decision(categorie_risque)` → `decision`
5. Si `client_id` fourni : `crud.create_prediction(db, ...)` → persiste

**Response 200** :
```json
{
  "cout_predit": 12543.67,
  "categorie_risque": "moyen",
  "score_risque": 0.74,
  "prime": 14425.22,
  "decision": "accepter",
  "prediction_id": 1
}
```

**prediction_id** : `null` si pas de persistance (pas de client_id), entier si persisté.

**Errors** :
- `400` : client_id fourni mais client inexistant ou inactif
- `422` : champs ML invalides
- `500` : modèle .pkl absent
