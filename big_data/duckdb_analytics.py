"""
Module analytique Big Data — lecture DuckDB sur Parquet.

Classe DuckDBAnalytics : 9 méthodes retournant des DataFrames Pandas.
Chaque requête interroge le Parquet en lecture directe via DuckDB
(pas de chargement en base PostgreSQL, pas de chargement en RAM).

Pourquoi DuckDB plutôt que pandas.read_parquet() ?
    pandas chargerait les 5M lignes × 14 colonnes entièrement en RAM (~800 Mo).
    DuckDB lit uniquement les colonnes nécessaires à la requête (format colonne)
    et retourne un petit DataFrame agrégé de quelques lignes — beaucoup plus
    rapide et économe en mémoire.
"""

import duckdb
import pandas as pd


class DuckDBAnalytics:
    """Interface analytique DuckDB sur le Parquet insurance_big.parquet."""

    def __init__(self, parquet_path: str):
        """Initialise la connexion DuckDB in-memory.

        duckdb.connect() sans argument crée une base in-memory temporaire :
        elle n'écrit rien sur disque, elle sert uniquement de moteur SQL
        pour interroger le fichier Parquet externe.

        Args:
            parquet_path: Chemin vers le fichier Parquet (lecture seule).
        """
        self._path = parquet_path
        # Connexion DuckDB in-memory : moteur SQL léger, pas de base persistante
        self._conn = duckdb.connect()

    def _q(self, sql: str) -> pd.DataFrame:
        """Exécute une requête SQL et retourne un DataFrame Pandas.

        Méthode interne mutualisée pour éviter de répéter
        self._conn.execute(...).df() dans chaque méthode publique.
        """
        return self._conn.execute(sql).df()

    def _src(self) -> str:
        """Retourne la clause FROM lisant le Parquet.

        read_parquet() est une fonction table DuckDB : elle expose le fichier
        Parquet comme une table SQL virtuelle sans le charger entièrement.
        DuckDB lit uniquement les colonnes utilisées dans la requête (pushdown).
        """
        return f"read_parquet('{self._path}')"

    def stats_par_region(self) -> pd.DataFrame:
        """Statistiques de cout_predit agrégées par région.

        Returns:
            DataFrame avec colonnes : region, nb, cout_moy, cout_med,
            cout_std, cout_min, cout_max. Trié par cout_moy DESC.
        """
        return self._q(
            f"""
            SELECT
                region,
                COUNT(*) AS nb,
                ROUND(AVG(cout_predit), 2) AS cout_moy,
                ROUND(MEDIAN(cout_predit), 2) AS cout_med,
                ROUND(STDDEV(cout_predit), 2) AS cout_std,
                ROUND(MIN(cout_predit), 2) AS cout_min,
                ROUND(MAX(cout_predit), 2) AS cout_max
            FROM {self._src()}
            GROUP BY region
            ORDER BY cout_moy DESC
        """
        )

    def stats_par_tranche_age(self) -> pd.DataFrame:
        """Statistiques de cout_predit agrégées par tranche d'âge.

        Le ORDER BY utilise CASE pour trier selon l'ordre métier des tranches
        (jeune → adulte → senior → senior+) plutôt que par ordre alphabétique.

        Returns:
            DataFrame avec colonnes : tranche_age, nb, cout_moy, cout_med,
            cout_std, cout_min, cout_max. Trié par ordre naturel des tranches.
        """
        return self._q(
            f"""
            SELECT
                tranche_age,
                COUNT(*) AS nb,
                ROUND(AVG(cout_predit), 2) AS cout_moy,
                ROUND(MEDIAN(cout_predit), 2) AS cout_med,
                ROUND(STDDEV(cout_predit), 2) AS cout_std,
                ROUND(MIN(cout_predit), 2) AS cout_min,
                ROUND(MAX(cout_predit), 2) AS cout_max
            FROM {self._src()}
            GROUP BY tranche_age
            ORDER BY
                CASE tranche_age
                    WHEN 'jeune'   THEN 1
                    WHEN 'adulte'  THEN 2
                    WHEN 'senior'  THEN 3
                    WHEN 'senior+' THEN 4
                END
        """
        )

    def stats_par_fumeur(self) -> pd.DataFrame:
        """Comparaison fumeurs vs non-fumeurs.

        Returns:
            DataFrame avec colonnes : fumeur, nb, cout_moy, score_risque_moy.
        """
        return self._q(
            f"""
            SELECT
                fumeur,
                COUNT(*) AS nb,
                ROUND(AVG(cout_predit), 2) AS cout_moy,
                ROUND(AVG(score_risque), 4) AS score_risque_moy
            FROM {self._src()}
            GROUP BY fumeur
            ORDER BY fumeur ASC
        """
        )

    def distribution_cout(self) -> pd.DataFrame:
        """Histogramme de cout_predit avec bins de 5 000 USD.

        Technique du binning SQL : FLOOR(x / 5000) * 5000 arrondit chaque
        valeur au multiple de 5000 inférieur.
        Ex : 7 300 → FLOOR(7300/5000)*5000 = 1*5000 = 5000 → bin [5000, 10000[

        Returns:
            DataFrame avec colonnes : bin_min, bin_max, nb. Trié par bin_min.
        """
        return self._q(
            f"""
            SELECT
                CAST(FLOOR(cout_predit / 5000) * 5000 AS INTEGER) AS bin_min,
                CAST(FLOOR(cout_predit / 5000) * 5000 + 5000 AS INTEGER) AS bin_max,
                COUNT(*) AS nb
            FROM {self._src()}
            GROUP BY bin_min, bin_max
            ORDER BY bin_min
        """
        )

    def percentiles_cout(self) -> pd.DataFrame:
        """Percentiles de cout_predit (P10 à P99).

        PERCENTILE_CONT est une fonction d'ordre SQL : elle trie toutes les
        valeurs et retourne celle au rang demandé (interpolation continue).
        Ex : P50 = médiane = valeur qui coupe la distribution en deux moitiés.

        Returns:
            DataFrame avec 1 ligne et colonnes : p10, p25, p50, p75, p90, p95, p99.
        """
        # Variable intermédiaire pour raccourcir les lignes SQL
        pct = "WITHIN GROUP (ORDER BY cout_predit)"
        return self._q(
            f"""
            SELECT
                ROUND(PERCENTILE_CONT(0.10) {pct}, 2) AS p10,
                ROUND(PERCENTILE_CONT(0.25) {pct}, 2) AS p25,
                ROUND(PERCENTILE_CONT(0.50) {pct}, 2) AS p50,
                ROUND(PERCENTILE_CONT(0.75) {pct}, 2) AS p75,
                ROUND(PERCENTILE_CONT(0.90) {pct}, 2) AS p90,
                ROUND(PERCENTILE_CONT(0.95) {pct}, 2) AS p95,
                ROUND(PERCENTILE_CONT(0.99) {pct}, 2) AS p99
            FROM {self._src()}
        """
        )

    def correlation_age_cout(self) -> pd.DataFrame:
        """Coût moyen prédit par âge (18 à 64).

        Retourne une ligne par âge entier — utile pour tracer une courbe
        et visualiser la progression du coût avec l'âge.

        Returns:
            DataFrame avec colonnes : age, cout_moy. Trié par age ASC.
        """
        return self._q(
            f"""
            SELECT
                age,
                ROUND(AVG(cout_predit), 2) AS cout_moy
            FROM {self._src()}
            GROUP BY age
            ORDER BY age
        """
        )

    def top_profils_risque(self) -> pd.DataFrame:
        """Top 10 combinaisons (tranche_age, categorie_imc, fumeur) par score_risque.

        GROUP BY sur 3 colonnes catégorielles : chaque combinaison unique forme
        un groupe (ex : senior+ / obese / True). On calcule le score_risque
        moyen de chaque groupe et on garde les 10 plus élevés.

        Returns:
            DataFrame avec colonnes : tranche_age, categorie_imc, fumeur,
            score_risque_moy, nb. 10 lignes, trié par score_risque_moy DESC.
        """
        return self._q(
            f"""
            SELECT
                tranche_age,
                categorie_imc,
                fumeur,
                ROUND(AVG(score_risque), 4) AS score_risque_moy,
                COUNT(*) AS nb
            FROM {self._src()}
            GROUP BY tranche_age, categorie_imc, fumeur
            ORDER BY score_risque_moy DESC
            LIMIT 10
        """
        )

    def evolution_imc_cout(self) -> pd.DataFrame:
        """Coût moyen par tranche d'IMC (bins de 2 points).

        Même technique de binning que distribution_cout() mais sur l'IMC :
        FLOOR(imc / 2) * 2 regroupe les IMC par tranches de 2 points.
        Ex : 27.4 → FLOOR(27.4/2)*2 = 13*2 = 26 → bin [26, 28[

        Returns:
            DataFrame avec colonnes : imc_bin, cout_moy. Trié par imc_bin.
        """
        return self._q(
            f"""
            SELECT
                ROUND(FLOOR(imc / 2) * 2, 0) AS imc_bin,
                ROUND(AVG(cout_predit), 2) AS cout_moy
            FROM {self._src()}
            GROUP BY imc_bin
            ORDER BY imc_bin
        """
        )

    def stats_globales(self) -> pd.DataFrame:
        """Statistiques globales du portefeuille (1 ligne).

        CAST(fumeur AS DOUBLE) convertit True→1.0 / False→0.0 avant d'appeler
        AVG, ce qui donne directement la proportion de fumeurs (entre 0 et 1).
        Multiplier par 100 donne le pourcentage.

        Returns:
            DataFrame avec colonnes : nb_total, cout_moy, score_risque_moy,
            age_moy, pct_fumeurs.
        """
        return self._q(
            f"""
            SELECT
                COUNT(*) AS nb_total,
                ROUND(AVG(cout_predit), 2) AS cout_moy,
                ROUND(AVG(score_risque), 4) AS score_risque_moy,
                ROUND(AVG(age), 1) AS age_moy,
                ROUND(AVG(CAST(fumeur AS DOUBLE)) * 100, 2) AS pct_fumeurs
            FROM {self._src()}
        """
        )
