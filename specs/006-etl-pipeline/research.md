# Research: ETL Pipeline 3 Sources

**Branch**: `006-etl-pipeline` | **Date**: 2026-05-04

## Décision 1 — Endpoint OpenWeatherMap : Current Weather vs 5-Day Forecast

**Decision**: `GET /weather` (Current Weather Data)

**Rationale**:
- Un seul appel par ville (4 appels total = bien dans le free tier à 1 000 req/jour)
- Retourne directement `main.temp`, `main.humidity`, `rain.1h` dans la même réponse
- Le forecast (5-day) retourne 40 points toutes les 3h → nécessiterait une moyenne supplémentaire et compliquerait `transform_meteo.py` sans valeur ajoutée pour la démo
- Les données courantes suffisent pour peupler `donnees_meteo` et démontrer C1

**Alternatives considérées**:
- `/forecast` (5-day) : écarté — complexité de moyennage non justifiée
- One Call API 3.0 : écarté — payant après 1 000 appels

**URL template**: `https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric`

---

## Décision 2 — Site cible du scraping

**Decision**: `santemagazine.fr`

**Rationale**:
- Site francophone grand public, thématique santé directement liée au dataset assurance
- Pas de paywall, pas d'authentification requise
- Structure HTML stable avec balises sémantiques (`article`, `h2`, `p`) — plus fiable que des sites purement journalistiques
- Argus de l'assurance cible les professionnels et est plus susceptible d'avoir des protections

**Alternatives considérées**:
- `argusdelassurance.com` : écarté — possible paywall et anti-bot plus agressif
- `ameli.fr` : écarté — site institutionnel, structure moins riche pour le scraping d'articles

**URL cible**: `https://www.santemagazine.fr/actualites` (liste d'articles)

---

## Décision 3 — Pattern d'insertion : ORM SQLAlchemy vs SQL brut

**Decision**: SQLAlchemy ORM via `database/models.py` existants

**Rationale**:
- Les modèles `DonneesMeteo` et `Article` sont déjà définis dans `database/models.py`
- L'ORM garantit la cohérence des types (Numeric, DateTime, Boolean) avec le schéma PostgreSQL
- Le pattern `ON CONFLICT DO NOTHING` est géré via `insert().on_conflict_do_nothing()` de SQLAlchemy Core (compatible avec l'ORM)
- La session SQLAlchemy est déjà testée en Feature 005

**Alternatives considérées**:
- `psycopg2` direct : écarté — pas de réutilisation des modèles existants, duplication de logique
- `pandas.to_sql` : écarté — ne gère pas `ON CONFLICT DO NOTHING` nativement

---

## Décision 4 — Détermination de la saison

**Decision**: Mapping mois → saison depuis `datetime.now()`

```python
SAISON_MAP = {
    12: "hiver", 1: "hiver", 2: "hiver",
    3: "printemps", 4: "printemps", 5: "printemps",
    6: "ete", 7: "ete", 8: "ete",
    9: "automne", 10: "automne", 11: "automne",
}
```

**Rationale**: Simple, déterministe, pas de dépendance externe. Correspond à la saisonnalité de l'hémisphère nord (US). Les valeurs correspondent exactement aux CHECK contraintes de la table `donnees_meteo`.

---

## Décision 5 — Backup JSON des données brutes

**Decision**: Un fichier horodaté par exécution (pas d'écrasement)

**Format**: `data/external/api_data/meteo_{YYYYMMDD_HHMMSS}.json` et `data/external/scraped_data/articles_{YYYYMMDD_HHMMSS}.json`

**Rationale**: Permet de rejouer une transformation si l'insertion échoue. L'horodatage évite l'écrasement entre exécutions. Conforme à SC-004 (backup avant insertion).

---

## Décision 6 — Gestion des erreurs réseau dans le scraper

**Decision**: `try/except requests.exceptions.RequestException` avec timeout=10s

**Rationale**:
- `requests.exceptions.RequestException` couvre ConnectionError, Timeout, HTTPError
- Timeout de 10 secondes : raisonnable pour un site public, évite les blocages indéfinis
- En cas d'échec : log de l'erreur + retour d'une liste vide (le loader ne fait rien, pas d'interruption)

---

## Décision 7 — Requêtes SQL dans queries.sql

**Plan des 10 requêtes** :

1. Jointure `clients × regions` — liste clients avec nom de région
2. COUNT clients par région (GROUP BY)
3. IMC moyen par région (AVG + GROUP BY)
4. Régions avec plus de 100 clients fumeurs (GROUP BY + HAVING)
5. Coût moyen prédit par catégorie de risque (jointure `clients × predictions`)
6. Clients sans aucune prédiction (NOT EXISTS / LEFT JOIN ... IS NULL)
7. Top 3 clients par coût prédit (sous-requête ou RANK)
8. Distribution fumeurs/non-fumeurs par région (GROUP BY multi-colonnes)
9. Clients avec contrats actifs et leur prime mensuelle moyenne (3 tables : clients + regions + contrats)
10. Statistiques complètes par région : nombre clients, IMC moyen, % fumeurs, coût prédit moyen (multi-agrégations)

Toutes exécutables sur la base peuplée avec 1 338 clients + 4 régions.
