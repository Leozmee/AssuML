# Data Model: AssuML — Système de Souscription Assurance Santé IA

**Feature**: 001-assuml-souscription-ia
**Date**: 2026-04-07

---

## Entités et Relations

```
regions (1) ──────────────────────────────────────── (*) clients
                                                           │
                                            ┌──────────────┤
                                            │              │
                                      predictions (*)  contrats (*)
                                                           │
                                                      sinistres (*)

regions (1) ──── (*) donnees_meteo

articles (standalone — pas de FK)
```

### Cardinalités
- `regions` → `clients` : 1 région a plusieurs clients (FK `region_id`)
- `clients` → `predictions` : 1 client a plusieurs prédictions (FK `client_id`, CASCADE)
- `clients` → `contrats` : 1 client a plusieurs contrats (FK `client_id`, CASCADE)
- `contrats` → `sinistres` : 1 contrat a plusieurs sinistres (FK `contrat_id`, CASCADE)
- `regions` → `donnees_meteo` : 1 région a plusieurs relevés météo (FK `region_id`)
- `articles` : entité autonome (pas de FK)

---

## Table : `regions`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| `region_id` | SERIAL | PK |
| `nom_region` | VARCHAR(50) | NOT NULL, UNIQUE |

**Données initiales** (INSERT INTO) :
- southwest, southeast, northwest, northeast

---

## Table : `clients`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| `client_id` | SERIAL | PK |
| `region_id` | INTEGER | FK → regions(region_id), NOT NULL |
| `age` | INTEGER | NOT NULL, CHECK (age BETWEEN 18 AND 120) |
| `sexe` | VARCHAR(10) | NOT NULL, CHECK (sexe IN ('homme', 'femme', 'autre')) |
| `imc` | DECIMAL(5,2) | NOT NULL, CHECK (imc BETWEEN 10.0 AND 80.0) |
| `enfants` | INTEGER | NOT NULL DEFAULT 0, CHECK (enfants BETWEEN 0 AND 20) |
| `fumeur` | BOOLEAN | NOT NULL DEFAULT FALSE |
| `email` | VARCHAR(255) | NULL (RGPD) |
| `telephone` | VARCHAR(20) | NULL (RGPD) |
| `date_creation` | TIMESTAMP | NOT NULL DEFAULT NOW() |
| `date_suppression` | TIMESTAMP | NULL (soft delete) |

**Index** :
- PK sur `client_id`
- FK index sur `region_id`
- Index partiel : `WHERE date_suppression IS NULL` (clients actifs)
- Index sur `fumeur` (filtre fréquent Analytics)

**Transitions d'état** :
- Actif : `date_suppression IS NULL`
- Supprimé (soft) : `date_suppression IS NOT NULL`

---

## Table : `predictions`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| `prediction_id` | SERIAL | PK |
| `client_id` | INTEGER | FK → clients(client_id) ON DELETE CASCADE, NOT NULL |
| `cout_predit` | DECIMAL(10,2) | NOT NULL, CHECK (cout_predit >= 0) |
| `score_risque` | DECIMAL(4,3) | NOT NULL, CHECK (score_risque BETWEEN 0 AND 1) |
| `categorie_risque` | VARCHAR(20) | NOT NULL, CHECK (categorie_risque IN ('faible','moyen','eleve','critique')) |
| `decision` | VARCHAR(20) | NOT NULL, CHECK (decision IN ('accepter','examiner','refuser')) |
| `prime` | DECIMAL(10,2) | NOT NULL, CHECK (prime >= 0) |
| `version_modele` | VARCHAR(50) | NOT NULL |
| `date_prediction` | TIMESTAMP | NOT NULL DEFAULT NOW() |

**Index** :
- PK sur `prediction_id`
- FK index sur `client_id`
- Index sur `date_prediction` (tri chronologique)
- Index sur `categorie_risque` (agrégation stats)

---

## Table : `contrats`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| `contrat_id` | SERIAL | PK |
| `client_id` | INTEGER | FK → clients(client_id) ON DELETE CASCADE, NOT NULL |
| `statut` | VARCHAR(20) | NOT NULL DEFAULT 'actif', CHECK (statut IN ('actif','suspendu','resilié','expiré')) |
| `prime_mensuelle` | DECIMAL(10,2) | NOT NULL, CHECK (prime_mensuelle > 0) |
| `date_debut` | DATE | NOT NULL |
| `date_fin` | DATE | NULL |
| `type_couverture` | VARCHAR(50) | NOT NULL, CHECK (type_couverture IN ('basique','standard','premium')) |
| `date_creation` | TIMESTAMP | NOT NULL DEFAULT NOW() |

**Index** :
- PK sur `contrat_id`
- FK index sur `client_id`
- Index sur `statut` (filtre fréquent)
- Index partiel : `WHERE statut = 'actif'`

**Transitions d'état** :
- `actif` → `suspendu` (impayé)
- `actif` / `suspendu` → `resilié` (résiliation volontaire)
- `actif` → `expiré` (date_fin dépassée)

---

## Table : `sinistres`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| `sinistre_id` | SERIAL | PK |
| `contrat_id` | INTEGER | FK → contrats(contrat_id) ON DELETE CASCADE, NOT NULL |
| `date_sinistre` | DATE | NOT NULL |
| `montant_sinistre` | DECIMAL(10,2) | NOT NULL, CHECK (montant_sinistre > 0) |
| `type_sinistre` | VARCHAR(50) | NOT NULL, CHECK (type_sinistre IN ('maladie','accident','hospitalisation','chirurgie','autre')) |
| `statut_sinistre` | VARCHAR(20) | NOT NULL DEFAULT 'en_cours', CHECK (statut_sinistre IN ('en_cours','instruit','clôturé','rejeté')) |
| `description` | TEXT | NULL |

**Index** :
- PK sur `sinistre_id`
- FK index sur `contrat_id`
- Index sur `statut_sinistre`
- Index sur `date_sinistre`

**Règle métier** : Un sinistre ne peut être créé que si le contrat associé
a le statut `actif` (vérification applicative dans le router FastAPI).

---

## Table : `donnees_meteo`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| `meteo_id` | SERIAL | PK |
| `region_id` | INTEGER | FK → regions(region_id), NOT NULL |
| `temperature_moy` | DECIMAL(5,2) | NOT NULL |
| `humidite_moy` | DECIMAL(5,2) | NOT NULL, CHECK (humidite_moy BETWEEN 0 AND 100) |
| `precipitations` | DECIMAL(7,2) | NOT NULL, CHECK (precipitations >= 0) |
| `saison` | VARCHAR(10) | NOT NULL, CHECK (saison IN ('hiver','printemps','ete','automne')) |
| `date_collecte` | TIMESTAMP | NOT NULL DEFAULT NOW() |

**Index** :
- PK sur `meteo_id`
- FK index sur `region_id`
- Index composite sur `(region_id, date_collecte)`

---

## Table : `articles`

| Colonne | Type | Contraintes |
|---------|------|-------------|
| `article_id` | SERIAL | PK |
| `titre` | VARCHAR(500) | NOT NULL |
| `url_source` | VARCHAR(1000) | NOT NULL, UNIQUE |
| `nom_source` | VARCHAR(100) | NOT NULL |
| `resume` | TEXT | NULL |
| `date_publication` | DATE | NULL |
| `date_scraping` | TIMESTAMP | NOT NULL DEFAULT NOW() |

**Index** :
- PK sur `article_id`
- UNIQUE sur `url_source` (déduplication)
- Index sur `date_scraping` (tri chronologique)
- Index sur `nom_source`

---

## Schéma Big Data (Parquet — lecture seule)

Fichier : `data/big_data/insurance_big.parquet` — 10 M lignes synthétiques.
Pas de MCD/MLD : table plate, usage analytique uniquement.

| Colonne | Type | Description |
|---------|------|-------------|
| `age` | INT | Âge (18–64) |
| `sex` | STRING | 'male' / 'female' |
| `bmi` | FLOAT | IMC |
| `children` | INT | Nombre d'enfants |
| `smoker` | STRING | 'yes' / 'no' |
| `region` | STRING | Une des 4 régions |
| `charges` | FLOAT | Coût médical annuel |
| `charges_log` | FLOAT | log(charges) — normalisation |
| `age_group` | STRING | '18-25', '26-35', '36-45', '46-55', '56-65' |
| `bmi_category` | STRING | 'sous-poids', 'normal', 'surpoids', 'obèse' |
| `risk_score` | FLOAT | Score 0–1 calculé synthétiquement |

---

## Objets de Valeur (Business Logic)

### CategorieRisque
```
faible   : cout_predit < 5 000
moyen    : 5 000 ≤ cout_predit < 15 000
eleve    : 15 000 ≤ cout_predit < 30 000
critique : cout_predit ≥ 30 000
```

### Decision
```
faible / moyen  → accepter
eleve           → examiner
critique        → refuser
```

### PrimeMensuelle
```
prime = cout_predit / 12 × coefficient_risque
coefficient_risque : faible=1.0, moyen=1.15, eleve=1.35, critique=1.60
```
