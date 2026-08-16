"""
Module 2 — Analytics Big Data.

Lecture directe du Parquet via DuckDB (exception documentée à l'architecture
Streamlit→FastAPI : données Big Data en lecture seule, pas de chargement PostgreSQL).
"""

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from big_data.duckdb_analytics import DuckDBAnalytics  # noqa: E402

CHEMIN_PARQUET = str(
    Path(__file__).parent.parent.parent / "data/big_data/insurance_big.parquet"
)
THEME = "plotly_white"

st.set_page_config(page_title="Analytics — AssuML", page_icon="📊", layout="wide")
st.title("📊 Analytics du portefeuille — Big Data")


# ── Connexion DuckDB (singleton session) ──────────────────────────────────────


@st.cache_resource
def charger_analytics():
    """Instancie DuckDBAnalytics une seule fois par session Streamlit."""
    if not Path(CHEMIN_PARQUET).exists():
        return None
    return DuckDBAnalytics(CHEMIN_PARQUET)


analytics = charger_analytics()

if analytics is None:
    st.error(
        "Fichier Parquet introuvable : `data/big_data/insurance_big.parquet`\n\n"
        "Générez-le d'abord avec :\n```\npython big_data/generate_synthetic.py\n```"
    )
    st.stop()


# ── Helpers de cache ──────────────────────────────────────────────────────────


@st.cache_data(ttl=300)
def get_stats_globales():
    """Cache stats_globales() pendant 5 minutes."""
    return analytics.stats_globales()


@st.cache_data(ttl=300)
def get_stats_region():
    return analytics.stats_par_region()


@st.cache_data(ttl=300)
def get_stats_fumeur():
    return analytics.stats_par_fumeur()


@st.cache_data(ttl=300)
def get_distribution():
    return analytics.distribution_cout()


@st.cache_data(ttl=300)
def get_correlation_age():
    return analytics.correlation_age_cout()


@st.cache_data(ttl=300)
def get_top_profils():
    return analytics.top_profils_risque()


@st.cache_data(ttl=300)
def get_percentiles():
    return analytics.percentiles_cout()


# ── Métriques globales ────────────────────────────────────────────────────────

stats = get_stats_globales().iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Profils analysés", f"{int(stats['nb_total']):,}")
c2.metric("Coût moyen prédit", f"{stats['cout_moy']:,.0f} $")
c3.metric("Score risque moyen", f"{stats['score_risque_moy']:.3f}")
c4.metric("Âge moyen", f"{stats['age_moy']:.1f} ans")
c5.metric("Fumeurs", f"{stats['pct_fumeurs']:.1f} %")

st.divider()

# ── Section 1 — Analyse par région ───────────────────────────────────────────

with st.expander("📍 Analyse par région", expanded=True):
    df_region = get_stats_region()

    col_g, col_t = st.columns([2, 1])
    with col_g:
        fig = px.bar(
            df_region,
            x="region",
            y="cout_moy",
            color="region",
            title="Coût moyen prédit par région",
            labels={"cout_moy": "Coût moyen ($)", "region": "Région"},
            template=THEME,
        )
        st.plotly_chart(fig, use_container_width=True)
    with col_t:
        st.dataframe(
            df_region[["region", "nb", "cout_moy", "cout_med"]].rename(
                columns={
                    "region": "Région",
                    "nb": "Nb clients",
                    "cout_moy": "Coût moy.",
                    "cout_med": "Médiane",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

# ── Section 2 — Impact du tabac ───────────────────────────────────────────────

with st.expander("🚬 Impact du tabac"):
    df_fumeur = get_stats_fumeur()
    df_fumeur["Statut"] = df_fumeur["fumeur"].map({True: "Fumeur", False: "Non-fumeur"})

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(
            df_fumeur,
            x="Statut",
            y="cout_moy",
            color="Statut",
            title="Coût moyen prédit",
            labels={"cout_moy": "Coût moyen ($)"},
            template=THEME,
        )
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        fig = px.bar(
            df_fumeur,
            x="Statut",
            y="score_risque_moy",
            color="Statut",
            title="Score risque moyen",
            labels={"score_risque_moy": "Score risque [0-1]"},
            template=THEME,
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Section 3 — Distribution des coûts ───────────────────────────────────────

with st.expander("📊 Distribution des coûts"):
    df_dist = get_distribution()
    df_dist["label"] = df_dist["bin_min"].apply(lambda x: f"{x//1000}k$")

    fig = px.bar(
        df_dist,
        x="label",
        y="nb",
        title="Distribution des coûts prédits (bins 5 000 $)",
        labels={"label": "Tranche de coût", "nb": "Nombre de profils"},
        template=THEME,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Section 4 — Corrélation âge-coût ─────────────────────────────────────────

with st.expander("📈 Corrélation âge — coût prédit"):
    df_age = get_correlation_age()

    fig = px.line(
        df_age,
        x="age",
        y="cout_moy",
        title="Coût moyen prédit par âge",
        labels={"age": "Âge", "cout_moy": "Coût moyen ($)"},
        template=THEME,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Section 5 — Profils à risque ─────────────────────────────────────────────

with st.expander("⚠️ Top 10 profils à risque"):
    df_top = get_top_profils()
    df_top["fumeur"] = df_top["fumeur"].map({True: "Oui", False: "Non"})
    st.dataframe(
        df_top.rename(
            columns={
                "tranche_age": "Tranche âge",
                "categorie_imc": "Catégorie IMC",
                "fumeur": "Fumeur",
                "score_risque_moy": "Score risque moy.",
                "nb": "Nb profils",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

# ── Section 6 — Percentiles ───────────────────────────────────────────────────

with st.expander("📐 Percentiles du coût prédit"):
    perc = get_percentiles().iloc[0]
    cols = st.columns(7)
    for col, (label, val) in zip(
        cols,
        [
            ("P10", perc["p10"]),
            ("P25", perc["p25"]),
            ("P50", perc["p50"]),
            ("P75", perc["p75"]),
            ("P90", perc["p90"]),
            ("P95", perc["p95"]),
            ("P99", perc["p99"]),
        ],
    ):
        col.metric(label, f"{val:,.0f} $")

# ── Footer ────────────────────────────────────────────────────────────────────

st.divider()
st.caption("5 000 000 lignes analysées via DuckDB — lecture directe Parquet")
