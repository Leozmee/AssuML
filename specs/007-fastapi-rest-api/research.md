# Research: API REST FastAPI complète

**Feature**: 007-fastapi-rest-api | **Date**: 2026-05-04

## Décision 1 : Chargement des modèles ML

**Decision**: Chargement via mécanisme `lifespan` FastAPI au démarrage de l'application, en déclenchant explicitement les singletons de `ml_models/prediction/predict.py`.

**Rationale**: `predict.py` utilise déjà un pattern singleton (`_pipeline = None` initialisé au premier appel). Le `lifespan` FastAPI permet de garantir que les modèles sont chargés **avant** la première requête, et non au premier appel ML (ce qui ajouterait une latence inattendue). Si un `.pkl` est absent, l'API échoue au démarrage avec un message clair plutôt qu'à l'exécution de la première prédiction.

**Alternatives considered**:
- Import direct au niveau module `api/main.py` : fonctionnel mais couplage fort.
- Middleware de lazy loading : complexité inutile, les modèles sont toujours nécessaires.

---

## Décision 2 : Séparation schemas/ vs models/

**Decision**: Les schémas Pydantic v2 vivent dans `api/schemas/` et sont indépendants des modèles ORM SQLAlchemy de `database/models.py`. La conversion ORM → Pydantic se fait via `model_validate()` avec `from_attributes=True`.

**Rationale**: Les modèles ORM et les schémas API ont des cycles de vie différents — un modèle ORM peut exposer des champs internes (ex. `date_suppression`) qui ne doivent pas être retournés dans l'API. Pydantic v2 permet `model_config = ConfigDict(from_attributes=True)` pour la conversion automatique depuis les objets SQLAlchemy.

**Alternatives considered**:
- Utiliser directement les modèles ORM comme schémas : impossible avec Pydantic v2 sans configuration, et dangereux (exposition de champs internes).
- Schémas dans `database/schemas.py` : violation du SRP — les schémas API appartiennent à la couche API.

---

## Décision 3 : Gestion des dépendances FastAPI

**Decision**: `get_db()` generator dans `api/dependencies.py`, injecté via `Depends(get_db)` dans chaque endpoint qui nécessite la BDD.

**Rationale**: Pattern standard FastAPI pour la gestion du cycle de vie des sessions SQLAlchemy. Garantit que la session est fermée après chaque requête, même en cas d'exception. `crud.py` existant reçoit déjà la session en paramètre — compatibilité directe.

**Alternatives considered**:
- Session globale : non thread-safe, problèmes de connexions fantômes.
- `contextmanager` manuel dans chaque endpoint : redondance, risque d'oubli de `finally: db.close()`.

---

## Décision 4 : Encodage des paramètres ML dans PredictRequest

**Decision**: `PredictRequest` utilise `sexe: int` (0=homme, 1=femme) et `fumeur: int` (0=non, 1=oui) pour rester cohérent avec les colonnes d'entraînement de `predict.py`.

**Rationale**: `predict_cost()` et `predict_risk()` attendent des entiers pour sexe et fumeur (encodage binaire identique à l'entraînement). Convertir en bool dans le schéma Pydantic puis re-convertir en int serait une friction inutile.

**Alternatives considered**:
- `sexe: Literal["homme", "femme"]` avec conversion interne : plus lisible mais ajoute une couche de transformation et risque de désynchronisation avec le REGION_MAPPING de predict.py.
- Utiliser les mêmes noms qu'en base (`sexe` en français) : retenu — cohérence avec la constitution (nommage français pour les variables métier).

---

## Décision 5 : Vérification contrat actif pour sinistres

**Decision**: L'endpoint `POST /sinistres` effectue un SELECT sur le contrat avant insertion. Si `statut != 'actif'` ou contrat inexistant → `HTTPException(status_code=400)`.

**Rationale**: La règle métier (sinistre uniquement sur contrat actif) doit être enforced côté API, pas côté base de données. La contrainte est logique, pas référentielle — elle ne peut pas être exprimée par une FK ou un CHECK SQL.

**Alternatives considered**:
- Trigger PostgreSQL : fonctionnel mais opaque, difficile à tester unitairement et à documenter dans Swagger.
- Validation côté Streamlit uniquement : insuffisant — l'API doit être la source de vérité.

---

## Décision 6 : Structure des KPIs

**Decision**: `GET /stats/kpis` retourne un objet JSON avec 5 métriques calculées à la volée via SQLAlchemy queries agrégées :
- `nb_clients_actifs` : COUNT WHERE date_suppression IS NULL
- `nb_contrats_actifs` : COUNT WHERE statut = 'actif'
- `sinistres_en_cours` : COUNT WHERE statut_sinistre = 'en_cours'
- `repartition_risque` : dict {categorie: count} depuis predictions
- `cout_moyen_predit` : AVG(cout_predit) depuis predictions (None si aucune prédiction)

**Rationale**: Données calculées en temps réel depuis la source de vérité (PostgreSQL). Pas de cache — le volume (1 338 clients max) ne justifie pas la complexité d'un cache.

**Alternatives considered**:
- Vue matérialisée PostgreSQL : surengineering pour le volume actuel.
- Calcul côté Streamlit : violerait la constitution §III (Streamlit ne doit pas accéder directement à PostgreSQL).
