# Contract: Endpoints Clients

**Router** : `api/routers/clients.py` | **Prefix** : `/api/clients`

---

## GET /api/clients

**Description** : Liste paginée des clients actifs.

**Query params** :
- `skip` (int, default=0) : décalage pagination
- `limit` (int, default=100, max=100) : nombre maximum de résultats

**Response 200** :
```json
[
  {
    "client_id": 1,
    "age": 45,
    "sexe": "homme",
    "imc": 32.5,
    "enfants": 2,
    "fumeur": true,
    "nom_region": "southeast",
    "email": null,
    "telephone": null,
    "date_creation": "2026-04-07T12:00:00"
  }
]
```

---

## GET /api/clients/{client_id}

**Response 200** : même structure que ci-dessus (objet unique).
**Response 404** : `{"detail": "Client introuvable"}`

---

## POST /api/clients

**Body** :
```json
{
  "age": 35,
  "sexe": "femme",
  "imc": 24.0,
  "enfants": 1,
  "fumeur": false,
  "region_id": 2,
  "email": "contact@exemple.com",
  "telephone": null
}
```

**Response 201** : objet ClientRead complet avec client_id généré.
**Response 422** : champ invalide (age hors 18–120, sexe invalide, etc.)

---

## PUT /api/clients/{client_id}

**Body** : champs partiels (tous optionnels) :
```json
{
  "imc": 26.5,
  "enfants": 2
}
```

**Response 200** : objet ClientRead mis à jour.
**Response 404** : client inexistant ou déjà supprimé.

---

## DELETE /api/clients/{client_id}

**Description** : Soft delete — positionne `date_suppression = NOW()`.

**Response 200** :
```json
{"message": "Client désactivé", "client_id": 42}
```

**Response 404** : client inexistant ou déjà désactivé.
