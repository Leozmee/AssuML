"""
Module 4 — Monitoring.

Santé API, métriques ML depuis metadata.json, drift simulé, KPIs.
"""

import json
import os
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils import api_client as api
from components.metrics import afficher_kpis, afficher_metriques_modele
from components.charts import graphique_metriques_ml

st.set_page_config(page_title="Monitoring — AssuML", page_icon="📈", layout="wide")
st.title("📈 Monitoring système et ML")


# ── Santé de l'API ─────────────────────────────────────────────────────────────

st.subheader("Santé du système")

col_refresh = st.columns([5, 1])
with col_refresh[1]:
    if st.button("Rafraîchir", use_container_width=True):
        st.rerun()

health, err_health = api.get_health()

col_api, col_db, col_ml = st.columns(3)

if err_health and "503" not in str(err_health):
    col_api.error("API : indisponible")
    col_db.error("BDD : inconnue")
    col_ml.error("Modèles ML : inconnus")
else:
    if health is None:
        # Santé dégradée mais réponse reçue
        health = {"status": "degraded", "database": "error", "models": "error"}

    def _indicateur(col, label: str, statut: str):
        if statut == "ok":
            col.success(f"✅ {label} : OK")
        else:
            col.error(f"❌ {label} : {statut.upper()}")

    _indicateur(col_api, "API FastAPI", "ok")
    _indicateur(col_db, "PostgreSQL", health.get("database", "?"))
    _indicateur(col_ml, "Modèles ML", health.get("models", "?"))

st.divider()

# ── KPIs globaux ───────────────────────────────────────────────────────────────

st.subheader("KPIs du portefeuille")

kpis, err_kpis = api.get_kpis()
if err_kpis:
    st.warning(f"KPIs indisponibles : {err_kpis}")
else:
    afficher_kpis(kpis)

st.divider()

# ── Métriques ML ───────────────────────────────────────────────────────────────

st.subheader("Performances des modèles ML")

META_PATH = os.path.join(
    os.path.dirname(__file__), "../../ml_models/saved_models/metadata.json"
)

meta = None
try:
    with open(META_PATH) as f:
        meta = json.load(f)
except FileNotFoundError:
    st.warning(
        "Fichier metadata.json introuvable — affichage des métriques par défaut."
    )
    meta = {
        "regression": {
            "algorithme": "GradientBoostingRegressor",
            "date_entrainement": "2026-05-04",
            "metriques_test": {"r2": 0.8533, "mae": 2666.63, "rmse": 4771.56},
            "metriques_cv": {"r2_mean": 0.8315, "r2_std": 0.0429},
        },
        "classification": {
            "algorithme": "GradientBoostingClassifier",
            "date_entrainement": "2026-05-04",
            "metriques_test": {
                "accuracy": 0.8918,
                "f1_macro": 0.8685,
                "precision_macro": 0.9036,
                "recall_macro": 0.8471,
            },
            "metriques_cv": {"accuracy_mean": 0.8871, "accuracy_std": 0.0166},
        },
    }

afficher_metriques_modele(meta)

st.plotly_chart(graphique_metriques_ml(meta), use_container_width=True)

st.divider()

# ── Drift detection (simulé) ───────────────────────────────────────────────────

st.subheader("Drift detection — Évolution des métriques dans le temps")
st.caption("Simulation d'une surveillance temporelle des métriques de production.")

import numpy as np  # noqa: E402

np.random.seed(42)
nb_semaines = 12
semaines = [f"S{i+1}" for i in range(nb_semaines)]
r2_drift = [0.853 - i * 0.003 + np.random.normal(0, 0.008) for i in range(nb_semaines)]
accuracy_drift = [
    0.892 - i * 0.002 + np.random.normal(0, 0.006) for i in range(nb_semaines)
]
mae_drift = [2666 + i * 45 + np.random.normal(0, 80) for i in range(nb_semaines)]

df_drift = pd.DataFrame({
    "Semaine": semaines,
    "R² Régression": r2_drift,
    "Accuracy Classification": accuracy_drift,
    "MAE Régression ($)": mae_drift,
})

col_d1, col_d2 = st.columns(2)

with col_d1:
    fig_r2 = go.Figure()
    fig_r2.add_trace(go.Scatter(
        x=semaines, y=r2_drift, mode="lines+markers",
        name="R²", line=dict(color="#4e79a7", width=2),
    ))
    fig_r2.add_hline(y=0.80, line_dash="dash", line_color="red",
                     annotation_text="Seuil alerte R²=0.80")
    fig_r2.update_layout(
        title="R² Régression — Évolution", height=280,
        yaxis=dict(range=[0.75, 0.90]),
        margin=dict(t=40, b=20, l=20, r=20),
    )
    st.plotly_chart(fig_r2, use_container_width=True)

with col_d2:
    fig_acc = go.Figure()
    fig_acc.add_trace(go.Scatter(
        x=semaines, y=accuracy_drift, mode="lines+markers",
        name="Accuracy", line=dict(color="#59a14f", width=2),
    ))
    fig_acc.add_hline(y=0.85, line_dash="dash", line_color="red",
                      annotation_text="Seuil alerte Acc=0.85")
    fig_acc.update_layout(
        title="Accuracy Classification — Évolution", height=280,
        yaxis=dict(range=[0.80, 0.93]),
        margin=dict(t=40, b=20, l=20, r=20),
    )
    st.plotly_chart(fig_acc, use_container_width=True)

fig_mae = go.Figure()
fig_mae.add_trace(go.Bar(
    x=semaines, y=mae_drift,
    marker_color=[
        "#dc3545" if v > 3200 else ("#fd7e14" if v > 2800 else "#28a745")
        for v in mae_drift
    ],
))
fig_mae.update_layout(
    title="MAE Régression (USD) — par semaine",
    height=250,
    margin=dict(t=40, b=20, l=20, r=20),
)
st.plotly_chart(fig_mae, use_container_width=True)

st.caption(
    f"Version modèle : {meta.get('version', 'v1')} — "
    f"Split entraînement : {meta.get('split', '80/20')} — "
    f"Dernière mise à jour : {meta.get('date_mise_a_jour', '?')}"
)
