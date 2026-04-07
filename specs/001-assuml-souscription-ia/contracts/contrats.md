# Contrat API : Contrats et Sinistres

**Base URL**: `http://localhost:8000/api`
**Format**: JSON — Content-Type: application/json

---

## GET /api/contrats

**Query parameters** : `client_id` (optionnel), `statut` (optionnel), `limit`, `offset`.

**Response 200**:
```json
{
  "total": 5,
  "contrats": [
    {
      "contrat_id": 10,
      "client_id": 42,
      "statut": "actif",
      "prime_mensuelle": 3200.46,
      "date_debut": "2026-04-07",
      "date_fin": null,
      "type_couverture": "standard",
      "date_creation": "2026-04-07T10:00:00"
    }
  ]
}
```

---

## POST /api/contrats

**Request body**:
```json
{
  "client_id": 42,
  "prime_mensuelle": 3200.46,
  "date_debut": "2026-04-07",
  "type_couverture": "standard"
}
```

**Validation** :
- `client_id` : client actif existant (obligatoire)
- `prime_mensuelle` : > 0 (obligatoire)
- `date_debut` : date ISO (obligatoire)
- `type_couverture` : "basique", "standard" ou "premium" (obligatoire)

**Response 201** : objet contrat créé avec `statut = "actif"`.

---

## PUT /api/contrats/{contrat_id}

**Description**: Mise à jour du statut ou des dates d'un contrat.

**Request body**:
```json
{
  "statut": "resilié",
  "date_fin": "2027-04-07"
}
```

**Response 200** : contrat mis à jour.

---

## GET /api/sinistres

**Query parameters** : `contrat_id` (optionnel), `statut_sinistre` (optionnel), `limit`, `offset`.

**Response 200**:
```json
{
  "total": 2,
  "sinistres": [
    {
      "sinistre_id": 1,
      "contrat_id": 10,
      "date_sinistre": "2026-05-01",
      "montant_sinistre": 1500.00,
      "type_sinistre": "maladie",
      "statut_sinistre": "en_cours",
      "description": "Hospitalisation 3 jours"
    }
  ]
}
```

---

## POST /api/sinistres

**Request body**:
```json
{
  "contrat_id": 10,
  "date_sinistre": "2026-05-01",
  "montant_sinistre": 1500.00,
  "type_sinistre": "maladie",
  "description": "Hospitalisation 3 jours"
}
```

**Validation** :
- `contrat_id` : contrat avec statut `actif` (obligatoire)
- `montant_sinistre` : > 0 (obligatoire)
- `type_sinistre` : maladie/accident/hospitalisation/chirurgie/autre
- Si contrat non actif → **Response 400** :
  ```json
  {"detail": "Impossible de déclarer un sinistre sur un contrat non actif"}
  ```

**Response 201** : objet sinistre créé avec `statut_sinistre = "en_cours"`.

---

## PUT /api/sinistres/{sinistre_id}

**Description**: Mise à jour du statut d'un sinistre.

**Request body**:
```json
{
  "statut_sinistre": "clôturé"
}
```

**Response 200** : sinistre mis à jour.
