# Research: Big Data — DuckDB + Parquet 5M lignes

**Feature**: 009-bigdata-duckdb-parquet  
**Date**: 2026-06-01  
**Status**: Complet — toutes les décisions résolues

## Décisions techniques

### 1. Génération des données synthétiques

**Decision**: NumPy vectorisé (pas de boucles Python) + Pandas pour l'assemblage + PyArrow pour l'écriture.

**Rationale**: NumPy génère 5M valeurs en quelques secondes ; PyArrow écrit le Parquet sans passer par Pandas `to_parquet` natif (plus rapide, compression snappy par défaut). L'approche vectorisée garantit < 2 minutes d'exécution.

**Alternatives considérées**: Faker (trop lent pour 5M lignes), Polars (non installé dans le projet).

---

### 2. Formule de génération des charges

**Decision**: Formule linéaire calibrée sur les coefficients de régression du vrai dataset, avec bruit gaussien :

```
charges = 256*age + 339*bmi + 475*children + 23800*smoker_flag
        - 130*sex_female_flag - 12500
        + N(0, 4500)
```
Clipping entre 1 121 et 63 770 USD (min/max du vrai CSV).

**Rationale**: Reproduit les corrélations statistiques réelles (corrélation fumeur~charges > 0.7 dans le vrai dataset). Le bruit gaussien std=4 500 est calibré pour maintenir la variabilité sans casser les corrélations.

**Alternatives considérées**: Tirage aléatoire pur (rejeté — corrélations nulles, non réaliste pour un dataset d'assurance).

---

### 3. Connexion DuckDB

**Decision**: Connexion unique `duckdb.connect()` maintenue pendant la session Streamlit (pas d'ouverture/fermeture par requête). Instance mise en cache via `st.cache_resource` (ressource partagée, pas de TTL).

**Rationale**: `st.cache_resource` est conçu pour les connexions de base de données — partagé entre reruns et utilisateurs. `st.cache_data` avec TTL=300 est utilisé pour cacher les DataFrames résultats (évite de re-requêter à chaque rerun Streamlit).

**Alternatives considérées**: Ouverture/fermeture par requête (plus simple mais overhead inutile sur 5M lignes).

---

### 4. Interface DuckDBAnalytics

**Decision**: Classe avec `__init__(parquet_path: str)` stockant le chemin. Chaque méthode ouvre une requête sur `self._conn` (connexion DuckDB in-memory). Pas de chargement complet du Parquet en mémoire.

```python
class DuckDBAnalytics:
    def __init__(self, parquet_path: str):
        self._path = parquet_path
        self._conn = duckdb.connect()

    def stats_par_region(self) -> pd.DataFrame:
        return self._conn.execute(f"""
            SELECT region, COUNT(*) as nb, ...
            FROM read_parquet('{self._path}')
            GROUP BY region
        """).df()
```

**Rationale**: DuckDB `read_parquet()` lit le fichier en streaming colonne par colonne — pas de chargement en RAM du fichier entier. Chaque requête agrégée retourne quelques KB de résultat.

**Alternatives considérées**: Pandas `read_parquet()` (charge 5M lignes en RAM ~800 Mo — non viable sur machine modeste).

---

### 5. Caching Streamlit

**Decision**: Double cache :
- `st.cache_resource` : connexion `DuckDBAnalytics` (singleton session)
- `st.cache_data(ttl=300)` : résultats des 9 méthodes (rafraîchis toutes les 5 minutes)

**Rationale**: Séparer la ressource (connexion) des données (résultats) est le pattern recommandé par Streamlit pour les connexions DB.

---

### 6. Gitignore

**Decision**: Ajouter `data/big_data/` au `.gitignore` existant (cohérent avec l'entrée `*.parquet` déjà présente d'après la constitution).

**Rationale**: Principe IV de la constitution — les fichiers binaires `.parquet` ne doivent jamais être commités.

---

### 7. Tests

**Decision**: Tests unitaires dans `tests/unit/test_duckdb_analytics.py` avec un Parquet minimal généré en fixture (1 000 lignes, même schéma) pour éviter de dépendre du fichier 5M lignes dans les tests.

**Rationale**: Tests rapides, indépendants du script de génération, exécutables en CI sans le gros fichier.
