"""
Module 2 — Analytics.

KPIs globaux via GET /api/stats/kpis.
Placeholder Big Data — sera complété avec DuckDB dans la Feature 8.
"""

import streamlit as st

from utils import api_client as api
from components.metrics import afficher_kpis
from components.charts import graphique_repartition_risque

st.set_page_config(page_title="Analytics — AssuML", page_icon="📊", layout="wide")
st.title("📊 Analytics du portefeuille")

# ── KPIs globaux ───────────────────────────────────────────────────────────────

st.subheader("KPIs en temps réel")

kpis, err = api.get_kpis()
if err:
    st.error(f"Impossible de charger les KPIs : {err}")
    st.stop()

afficher_kpis(kpis)

st.divider()

# ── Répartition du risque ─────────────────────────────────────────────────────

col_chart, col_detail = st.columns([2, 1])

with col_chart:
    repartition = kpis.get("repartition_risque", {})
    if any(v > 0 for v in repartition.values()):
        st.plotly_chart(
            graphique_repartition_risque(repartition), use_container_width=True
        )
    else:
        st.info(
            "Aucune prédiction enregistrée — lancez des scorings depuis le module 1."
        )

with col_detail:
    st.markdown("**Répartition détaillée**")
    total = sum(repartition.values()) or 1
    for cat, val in repartition.items():
        pct = val / total * 100
        st.write(f"**{cat.capitalize()}** : {val} ({pct:.1f}%)")
        st.progress(int(pct))

st.divider()

# ── Placeholder Big Data ───────────────────────────────────────────────────────

st.subheader("Big Data — Analyse sur 10 M de lignes")

st.info(
    "**Disponible après intégration Big Data (Feature 8).**\n\n"
    "Cette section sera alimentée par DuckDB via lecture directe du fichier "
    "`data/big_data/insurance_big.parquet` (10 millions de lignes synthétiques).\n\n"
    "Fonctionnalités prévues :\n"
    "- Distribution des coûts sur le grand jeu de données\n"
    "- Corrélations IMC × coût × risque à grande échelle\n"
    "- Comparaison cohortes fumeurs / non-fumeurs par région\n"
    "- Segmentation géographique interactive\n"
    "- Performance de lecture DuckDB vs Pandas",
    icon="🚧",
)

with st.expander("Aperçu de l'architecture Big Data prévue"):
    st.code(
        """
# Lecture DuckDB (Feature 8 — 2_analytics.py)
import duckdb

conn = duckdb.connect()
df = conn.execute(\"\"\"
    SELECT region, fumeur,
           AVG(charges) as cout_moyen,
           COUNT(*) as nb_assures
    FROM 'data/big_data/insurance_big.parquet'
    GROUP BY region, fumeur
    ORDER BY cout_moyen DESC
\"\"\").df()
        """,
        language="python",
    )
