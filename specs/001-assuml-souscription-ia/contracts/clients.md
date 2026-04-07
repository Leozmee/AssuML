# Contrat API : Clients

**Base URL**: `http://localhost:8000/api/clients`
**Format**: JSON — Content-Type: application/json

---

## GET /api/clients

**Description**: Liste les clients actifs (date_suppression IS NULL).

**Query parameters** :
| Paramètre | Type | Optionnel | Description |
|-----------|------|-----------|-------------|
| `region` | string | oui | Filtrer par nom de région |
| `fumeur` | boolean | oui | Filtrer par statut fumeur |
| `categorie_risque` | string | oui | Filtrer par catégorie (faible/moyen/eleve/critique) |
| `limit` | int | oui | Nombre max de résultats (défaut: 100) |
| `offset` | int | oui | Pagination (défaut: 0) |

**Response 200**:
```json
{
  "total": 42,
  "clients": [
    {
      "client_id": 1,
      "region": "southwest",
      "age": 35,
      "sexe": "homme",
      "imc": 28.5,
      "enfants": 2,
      "fumeur": false,
      "email": null,
      "telephone": null,
      "date_creation": "2026-04-07T10:00:00"
    }
  ]
}
```

---

## GET /api/clients/{client_id}

**Description**: Détails d'un client (actif ou supprimé).

**Response 200**:
```json
{
  "client_id": 1,
  "region": "southwest",
  "age": 35,
  "sexe": "homme",
  "imc": 28.5,
  "enfants": 2,
  "fumeur": false,
  "email": null,
  "telephone": null,
  "date_creation": "2026-04-07T10:00:00",
  "date_suppression": null,
  "predictions": [],
  "contrats": []
}
```

**Response 404**:
```json
{"detail": "Client non trouvé"}
```

---

## POST /api/clients

**Description**: Crée un nouveau client.

**Request body**:
```json
{
  "region": "southwest",
  "age": 35,
  "sexe": "homme",
  "imc": 28.5,
  "enfants": 2,
  "fumeur": false,
  "email": "leo@exemple.fr",
  "telephone": null
}
```

**Validation** :
- `age` : entier entre 18 et 120 (obligatoire)
- `sexe` : "homme", "femme" ou "autre" (obligatoire)
- `imc` : décimal entre 10.0 et 80.0 (obligatoire)
- `enfants` : entier entre 0 et 20 (obligatoire)
- `fumeur` : booléen (obligatoire)
- `region` : une des 4 régions (obligatoire)
- `email`, `telephone` : optionnels

**Response 201**:
```json
{
  "client_id": 42,
  "region": "southwest",
  "age": 35,
  "sexe": "homme",
  "imc": 28.5,
  "enfants": 2,
  "fumeur": false,
  "email": "leo@exemple.fr",
  "telephone": null,
  "date_creation": "2026-04-07T10:00:00"
}
```

**Response 422** (validation échouée) :
```json
{
  "detail": [
    {
      "loc": ["body", "imc"],
      "msg": "imc doit être entre 10.0 et 80.0",
      "type": "value_error"
    }
  ]
}
```

---

## PUT /api/clients/{client_id}

**Description**: Modifie un client existant (actif uniquement).

**Request body** (tous les champs optionnels) :
```json
{
  "imc": 30.0,
  "enfants": 3
}
```

**Response 200** : objet client mis à jour.
**Response 404** : client non trouvé ou déjà supprimé.

---

## DELETE /api/clients/{client_id}

**Description**: Soft delete — renseigne `date_suppression`, ne supprime pas physiquement.

**Response 200**:
```json
{
  "message": "Client 42 supprimé (soft delete)",
  "date_suppression": "2026-04-07T10:30:00"
}
```

**Response 404** : client non trouvé ou déjà supprimé.

---

## GET /api/stats/kpis

**Description**: KPIs globaux sur les clients et prédictions.

**Response 200**:
```json
{
  "total_clients_actifs": 42,
  "total_contrats_actifs": 38,
  "total_sinistres_en_cours": 5,
  "repartition_risque": {
    "faible": 15,
    "moyen": 18,
    "eleve": 7,
    "critique": 2
  },
  "cout_moyen_predit": 12450.50
}
```
