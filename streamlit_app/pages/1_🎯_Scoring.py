"""
Module 1 — Scoring ML.

Formulaire de saisie d'un profil assuré → appels aux 3 endpoints predict.
Jauges Plotly + décision colorée.
"""

import streamlit as st

from utils import api_client as api
from components.charts import jauge_cout, jauge_risque, jauge_prime
from components.metrics import badge_decision

st.set_page_config(page_title="Scoring — AssuML", page_icon="🎯", layout="wide")
st.title("🎯 Scoring assurantiel")
st.caption(
    "Prédiction du coût médical, du risque et calcul de la prime à partir d'un profil."
)

REGIONS_LABEL = {
    "northeast": "Northeast",
    "northwest": "Northwest",
    "southeast": "Southeast",
    "southwest": "Southwest",
}
REGIONS_REVERSE = {v: k for k, v in REGIONS_LABEL.items()}

# ── Formulaire ─────────────────────────────────────────────────────────────────

with st.form("scoring_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.slider("Âge", 18, 90, 35)
        imc = st.slider("IMC", 10.0, 55.0, 25.0, step=0.1, format="%.1f")
    with col2:
        enfants = st.number_input("Enfants à charge", 0, 10, 0, step=1)
        sexe_label = st.radio("Sexe", ["Homme", "Femme"], horizontal=True)
        fumeur_label = st.radio("Fumeur", ["Non", "Oui"], horizontal=True)
    with col3:
        region_label = st.selectbox("Région", list(REGIONS_LABEL.values()))
        st.write("")
        client_id_opt = st.number_input(
            "Client ID (optionnel — persiste la prédiction)",
            min_value=0,
            value=0,
            step=1,
            help="Laissez à 0 pour une prédiction anonyme.",
        )

    col_b1, col_b2, col_b3 = st.columns(3)
    btn_complet = col_b1.form_submit_button(
        "Scoring complet", use_container_width=True, type="primary"
    )
    btn_cout = col_b2.form_submit_button("Coût seul", use_container_width=True)
    btn_risque = col_b3.form_submit_button("Risque seul", use_container_width=True)


# ── Payload commun ────────────────────────────────────────────────────────────


def build_payload():
    region_key = REGIONS_REVERSE[region_label]
    payload = {
        "age": age,
        "sexe": 0 if sexe_label == "Homme" else 1,
        "imc": imc,
        "enfants": enfants,
        "fumeur": 0 if fumeur_label == "Non" else 1,
        "region": region_key,
    }
    if client_id_opt > 0:
        payload["client_id"] = int(client_id_opt)
    return payload


# ── Scoring complet ────────────────────────────────────────────────────────────

if btn_complet:
    payload = build_payload()
    with st.spinner("Calcul en cours..."):
        data, err = api.predict_complet(payload)

    if err:
        st.error(f"Erreur API : {err}")
    else:
        st.divider()

        # Décision banner
        decision_html = badge_decision(data["decision"])
        st.markdown(
            f"<div style='text-align:center;padding:16px;font-size:1.4em;'>"
            f"Décision : {decision_html}</div>",
            unsafe_allow_html=True,
        )

        # 3 jauges côte à côte
        gc, gr, gp = st.columns(3)
        with gc:
            st.plotly_chart(jauge_cout(data["cout_predit"]), use_container_width=True)
        with gr:
            st.plotly_chart(
                jauge_risque(data["score_risque"], data["categorie_risque"]),
                use_container_width=True,
            )
        with gp:
            st.plotly_chart(jauge_prime(data["prime"]), use_container_width=True)

        # Détails
        with st.expander("Détails de la prédiction"):
            col1, col2 = st.columns(2)
            col1.metric("Coût médical prédit", f"${data['cout_predit']:,.2f}")
            col1.metric("Prime mensuelle", f"${data['prime']:,.2f}")
            col2.metric("Catégorie de risque", data["categorie_risque"].upper())
            col2.metric("Score de risque", f"{data['score_risque']:.1%}")
            if data.get("prediction_id"):
                pid = data["prediction_id"]
                st.caption(f"Prédiction persistée en base — ID : {pid}")

# ── Coût seul ──────────────────────────────────────────────────────────────────

if btn_cout:
    payload = build_payload()
    with st.spinner("Calcul du coût..."):
        data, err = api.predict_cout(payload)

    if err:
        st.error(f"Erreur API : {err}")
    else:
        st.divider()
        st.markdown("### Coût médical prédit")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Coût prédit", f"${data['cout_predit']:,.2f}")
        with col2:
            st.plotly_chart(jauge_cout(data["cout_predit"]), use_container_width=True)

# ── Risque seul ────────────────────────────────────────────────────────────────

if btn_risque:
    payload = build_payload()
    with st.spinner("Calcul du risque..."):
        data, err = api.predict_risque(payload)

    if err:
        st.error(f"Erreur API : {err}")
    else:
        st.divider()
        st.markdown("### Catégorie de risque")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Catégorie", data["categorie_risque"].upper())
            st.metric("Score", f"{data['score_risque']:.1%}")
        with col2:
            st.plotly_chart(
                jauge_risque(data["score_risque"], data["categorie_risque"]),
                use_container_width=True,
            )
