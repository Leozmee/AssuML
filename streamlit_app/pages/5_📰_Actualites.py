"""
Module 5 — Actualités et météo.

Articles scrappés (filtre source) + données météo (filtres région/saison).
"""

import streamlit as st

from utils import api_client as api
from components.tables import df_meteo

st.set_page_config(page_title="Actualités — AssuML", page_icon="📰", layout="wide")
st.title("📰 Actualités santé & données météo")

# ── Articles ───────────────────────────────────────────────────────────────────

st.subheader("Articles d'actualité santé")

# Charger une première fois pour extraire les sources disponibles
articles_init, _ = api.get_articles(limit=100)
items_init = (articles_init or {}).get("items", [])
sources_dispo = sorted(set(a["nom_source"] for a in items_init)) if items_init else []

col_source, col_btn = st.columns([3, 1])
with col_source:
    source_choisie = st.selectbox(
        "Filtrer par source",
        ["Toutes les sources"] + sources_dispo,
        key="articles_source",
    )
with col_btn:
    st.write("")
    st.write("")
    rafraichir = st.button("Rafraîchir", key="btn_refresh_articles")

source_param = None if source_choisie == "Toutes les sources" else source_choisie

articles, err = api.get_articles(source=source_param, limit=100)

if err:
    st.error(f"Impossible de charger les articles : {err}")
elif not articles or not articles.get("items"):
    st.info(
        "Aucun article disponible. Lancez le pipeline ETL pour alimenter cette section."
    )
    st.code("python -m data_pipeline.extract.scraper", language="bash")
else:
    items = articles["items"]
    total = articles.get("total", len(items))
    st.caption(f"{total} article(s) — affichage des {len(items)} plus récents.")

    for article in items:
        titre = article.get("titre", "Sans titre")
        source = article.get("nom_source", "?")
        date_pub = str(article.get("date_publication") or "")[:10]
        resume = article.get("resume") or ""
        url = article.get("url_source", "#")

        with st.expander(f"**{titre}** — {source} ({date_pub})"):
            col_info, col_lien = st.columns([4, 1])
            with col_info:
                if resume:
                    st.write(resume)
                else:
                    st.caption("Aucun résumé disponible.")
            with col_lien:
                st.markdown(f"[Lire l'article]({url})", unsafe_allow_html=False)
                st.caption(f"Scrappé le : {str(article.get('date_scraping', ''))[:10]}")

st.divider()

# ── Données météo ─────────────────────────────────────────────────────────────

st.subheader("Données météo régionales")

REGIONS_OPTIONS = ["Toutes", "northeast", "northwest", "southeast", "southwest"]
SAISONS_OPTIONS = ["Toutes", "hiver", "printemps", "ete", "automne"]

col_r, col_s = st.columns(2)
with col_r:
    region_choisie = st.selectbox("Région", REGIONS_OPTIONS, key="meteo_region")
with col_s:
    saison_choisie = st.selectbox("Saison", SAISONS_OPTIONS, key="meteo_saison")

region_param = None if region_choisie == "Toutes" else region_choisie
saison_param = None if saison_choisie == "Toutes" else saison_choisie

meteo, err_meteo = api.get_meteo(region=region_param, saison=saison_param, limit=100)

if err_meteo:
    st.error(f"Impossible de charger les données météo : {err_meteo}")
elif not meteo:
    st.info(
        "Aucune donnée météo disponible. "
        "Lancez le pipeline ETL pour alimenter cette section."
    )
    st.code("python -m data_pipeline.extract.api_extractor", language="bash")
else:
    df = df_meteo(meteo)
    st.dataframe(df, use_container_width=True, hide_index=True)

    import plotly.express as px
    if len(df) > 1:
        fig = px.scatter(
            df,
            x="Temp. moy (°C)",
            y="Précipitations (mm)",
            color="Région",
            symbol="Saison",
            size="Humidité moy (%)",
            hover_data=["Date collecte"],
            title="Température vs Précipitations par région",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)
