# Contrat API : Prédictions ML

**Base URL**: `http://localhost:8000/api`
**Format**: JSON — Content-Type: application/json

---

## POST /api/predict/cout

**Description**: Prédiction du coût médical annuel (régression).

**Request body**:
```json
{
  "age": 45,
  "sexe": "femme",
  "imc": 32.0,
  "enfants": 1,
  "fumeur": true,
  "region": "northeast"
}
```

**Response 200**:
```json
{
  "cout_predit": 28450.75,
  "version_modele": "v20260407-a1b2c3",
  "date_prediction": "2026-04-07T10:00:00"
}
```

**Response 422** : profil invalide (champ manquant ou hors plage).

---

## POST /api/predict/risque

**Description**: Classification du niveau de risque.

**Request body**: identique à `/api/predict/cout`.

**Response 200**:
```json
{
  "categorie_risque": "eleve",
  "score_risque": 0.847,
  "version_modele": "v20260407-a1b2c3",
  "date_prediction": "2026-04-07T10:00:00"
}
```

---

## POST /api/predict/complet

**Description**: Scoring complet — régression + classification + décision + prime.
Persiste le résultat dans la table `predictions` si `client_id` est fourni.

**Request body**:
```json
{
  "age": 45,
  "sexe": "femme",
  "imc": 32.0,
  "enfants": 1,
  "fumeur": true,
  "region": "northeast",
  "client_id": 42
}
```

(`client_id` optionnel — si absent, la prédiction n'est pas persistée.)

**Response 200**:
```json
{
  "prediction_id": 101,
  "client_id": 42,
  "cout_predit": 28450.75,
  "score_risque": 0.847,
  "categorie_risque": "eleve",
  "decision": "examiner",
  "prime": 3200.46,
  "version_modele": "v20260407-a1b2c3",
  "date_prediction": "2026-04-07T10:00:00"
}
```

**Calcul prime** :
`prime = cout_predit / 12 × coefficient_risque`
Coefficients : faible=1.0, moyen=1.15, eleve=1.35, critique=1.60

---

## GET /api/predictions

**Description**: Liste des prédictions (toutes ou filtrées par client).

**Query parameters** :
| Paramètre | Type | Optionnel | Description |
|-----------|------|-----------|-------------|
| `client_id` | int | oui | Filtrer par client |
| `categorie_risque` | string | oui | Filtrer par catégorie |
| `limit` | int | oui | Défaut: 50 |
| `offset` | int | oui | Défaut: 0 |

**Response 200**:
```json
{
  "total": 10,
  "predictions": [
    {
      "prediction_id": 101,
      "client_id": 42,
      "cout_predit": 28450.75,
      "score_risque": 0.847,
      "categorie_risque": "eleve",
      "decision": "examiner",
      "prime": 3200.46,
      "version_modele": "v20260407-a1b2c3",
      "date_prediction": "2026-04-07T10:00:00"
    }
  ]
}
```
