# Data Model: API REST FastAPI complète

**Feature**: 007-fastapi-rest-api | **Date**: 2026-05-04

> Les entités correspondent aux tables PostgreSQL existantes dans `database/models.py`.
> L'API ne crée pas de nouvelles tables — elle expose et orchestre les données existantes.

## Entités exposées par l'API

### Client
**Table** : `clients`
**Opérations** : GET liste, GET détail, POST créer, PUT modifier, DELETE soft

| Champ | Type | Contrainte | Notes |
|-------|------|------------|-------|
| client_id | int | PK, auto | Retourné à la création |
| region_id | int | FK regions | Lookup via nom_region dans PredictRequest |
| age | int | 18–120 | CHECK enforced en BDD et Pydantic |
| sexe | str | 'homme'/'femme' | Stocké en français |
| imc | float | 10.00–80.00 | Numeric(5,2) en BDD |
| enfants | int | >= 0 | |
| fumeur | bool | | True/False |
| email | str? | nullable | RGPD optionnel |
| telephone | str? | nullable | RGPD optionnel |
| date_creation | datetime | server_default=now() | |
| date_suppression | datetime? | NULL = actif | Soft delete |

**États** : actif (date_suppression IS NULL) / inactif (date_suppression NOT NULL)

---

### Prediction
**Table** : `predictions`
**Opérations** : POST (via /predict/complet si client_id fourni)

| Champ | Type | Contrainte | Notes |
|-------|------|------------|-------|
| prediction_id | int | PK, auto | |
| client_id | int? | FK clients nullable | Optionnel |
| cout_predit | float | > 0 | USD, sortie régression |
| score_risque | float | 0.0–1.0 | predict_proba max |
| categorie_risque | str | faible/moyen/eleve/critique | |
| decision | str | accepter/examiner/refuser | Depuis risk_engine |
| prime | float | > 0 | USD, depuis scoring |
| version_modele | str | | ex. "regression_v1" |
| date_prediction | datetime | server_default=now() | |

**Note** : Une prédiction peut exister sans client_id (scoring anonyme).

---

### Contrat
**Table** : `contrats`
**Opérations** : GET liste, POST créer, PUT modifier statut

| Champ | Type | Contrainte | Notes |
|-------|------|------------|-------|
| contrat_id | int | PK, auto | |
| client_id | int | FK clients | |
| statut | str | actif/cloture/suspendu | |
| prime_mensuelle | float | > 0 | USD |
| date_debut | date | | |
| date_fin | date? | nullable | |
| type_couverture | str | base/premium/excellence | |

**États** : actif → suspendu / cloture (transitions via PUT /contrats/{id}/statut)

---

### Sinistre
**Table** : `sinistres`
**Opérations** : GET liste, POST créer (contrat actif obligatoire), PUT modifier statut

| Champ | Type | Contrainte | Notes |
|-------|------|------------|-------|
| sinistre_id | int | PK, auto | |
| contrat_id | int | FK contrats | |
| date_sinistre | date | | |
| montant_sinistre | float | > 0 | USD |
| type_sinistre | str | hospitalisation/consultation/medicament/autre | |
| statut_sinistre | str | en_cours/rembourse/refuse | |
| description | str? | nullable | |

**Règle métier** : création uniquement si `contrats.statut = 'actif'` → 400 sinon.

---

### Article
**Table** : `articles`
**Opérations** : GET liste (filtre par source)

| Champ | Type | Contrainte | Notes |
|-------|------|------------|-------|
| article_id | int | PK, auto | |
| titre | str | max 500 | |
| url_source | str | UNIQUE | |
| nom_source | str | | ex. "santemagazine.fr" |
| resume | text? | nullable | Corps complet de l'article |
| date_publication | datetime? | nullable | |
| date_scraping | datetime | | |

---

### DonneesMeteo
**Table** : `donnees_meteo`
**Opérations** : GET liste (filtres région, saison)

| Champ | Type | Contrainte | Notes |
|-------|------|------------|-------|
| meteo_id | int | PK, auto | |
| region_id | int | FK regions | |
| temperature_moy | float | | Celsius |
| humidite_moy | float | 0–100 | % |
| precipitations | float | >= 0 | mm |
| saison | str | hiver/printemps/ete/automne | |
| date_collecte | datetime | server_default=now() | |

---

## Schémas Pydantic (séparés des ORM)

### PredictRequest
Entrée commune aux 3 endpoints ML :

| Champ | Type | Validation |
|-------|------|------------|
| age | int | 18 <= age <= 120 |
| sexe | int | 0 (homme) ou 1 (femme) |
| imc | float | 10.0 <= imc <= 80.0 |
| enfants | int | 0 <= enfants <= 10 |
| fumeur | int | 0 ou 1 |
| region | str | northeast/northwest/southeast/southwest |
| client_id | int? | None = prédiction anonyme (uniquement pour /predict/complet) |

### KPIsResponse
```json
{
  "nb_clients_actifs": 1338,
  "nb_contrats_actifs": 0,
  "sinistres_en_cours": 0,
  "repartition_risque": {"faible": 0, "moyen": 0, "eleve": 0, "critique": 0},
  "cout_moyen_predit": null
}
```

## Relations entre entités

```
regions (1) ──< clients (N)
regions (1) ──< donnees_meteo (N)
clients (1) ──< predictions (N)   [client_id nullable]
clients (1) ──< contrats (N)
contrats (1) ──< sinistres (N)    [contrat doit être actif]
```
