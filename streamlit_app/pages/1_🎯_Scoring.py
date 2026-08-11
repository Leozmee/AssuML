"""
Module 1 — Scoring ML.

Formulaire de saisie d'un profil assuré → appels aux 3 endpoints predict.
Jauges Plotly + décision colorée.
"""

import streamlit as st

from utils import api_client as api
from components.charts import jauge_cout, jauge_risque

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
        from business.scoring import COEFFICIENTS

        cout = data["cout_predit"]
        categorie = data["categorie_risque"]
        score = data["score_risque"]
        prime_annuelle = data["prime"]
        prime_mensuelle = prime_annuelle / 12
        cout_mensuel = cout / 12
        marge_annuelle = prime_annuelle - cout
        coefficient = COEFFICIENTS[categorie]
        decision = data["decision"]

        COULEURS_RISQUE = {
            "faible": "#28a745",
            "moyen": "#ffc107",
            "eleve": "#fd7e14",
            "critique": "#dc3545",
        }
        COULEURS_DECISION = {
            "accepter": "#28a745",
            "examiner": "#fd7e14",
            "refuser": "#dc3545",
        }

        st.divider()
        col1, col2, col3 = st.columns(3)

        # Section 1 — Prédiction ML
        with col1:
            st.markdown("#### Estimation ML du coût médical")
            st.metric("Coût annuel prédit", f"${cout:,.2f}")
            st.metric("Coût mensuel prédit", f"${cout_mensuel:,.2f}")

        # Section 2 — Profil de risque
        with col2:
            st.markdown("#### Profil de risque")
            couleur_risque = COULEURS_RISQUE.get(categorie, "#6c757d")
            st.markdown(
                f'<span style="background:{couleur_risque};color:white;'
                f"padding:4px 14px;border-radius:6px;font-weight:bold;"
                f'font-size:1.1em;">{categorie.upper()}</span>',
                unsafe_allow_html=True,
            )
            st.write("")
            st.metric("Score de risque", f"{score:.1%}")
            st.metric("Coefficient de marge", f"× {coefficient:.2f}")

        # Section 3 — Tarification
        with col3:
            st.markdown("#### Prime à facturer au client")
            st.metric(
                "Prime annuelle",
                f"${prime_annuelle:,.2f}",
                delta=f"+${marge_annuelle:,.2f} marge",
            )
            st.metric("Prime mensuelle", f"${prime_mensuelle:,.2f}")
            st.metric("Marge annuelle", f"${marge_annuelle:,.2f}")

        # Section 4 — Décision finale
        st.divider()
        couleur_dec = COULEURS_DECISION.get(decision, "#6c757d")
        _, col_dec, _ = st.columns([1, 2, 1])
        with col_dec:
            st.markdown(
                f"<div style='text-align:center;padding:20px;font-size:1.4em;'>"
                f"Décision finale : "
                f'<span style="background:{couleur_dec};color:white;'
                f'padding:6px 20px;border-radius:8px;font-weight:bold;">'
                f"{decision.upper()}</span></div>",
                unsafe_allow_html=True,
            )

        if data.get("prediction_id"):
            st.caption(f"Prédiction persistée en base — ID : {data['prediction_id']}")

# ── Coût seul ──────────────────────────────────────────────────────────────────

if btn_cout:
    payload = build_payload()
    with st.spinner("Calcul du coût..."):
        data, err = api.predict_cout(payload)

    if err:
        st.error(f"Erreur API : {err}")
    else:
        cout = data["cout_predit"]
        st.divider()
        st.markdown("#### Estimation ML du coût médical")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Coût annuel prédit", f"${cout:,.2f}")
            st.metric("Coût mensuel prédit", f"${cout / 12:,.2f}")
        with col2:
            st.plotly_chart(jauge_cout(cout), use_container_width=True)

# ── Risque seul ────────────────────────────────────────────────────────────────

if btn_risque:
    payload = build_payload()
    with st.spinner("Calcul du risque..."):
        data, err = api.predict_risque(payload)

    if err:
        st.error(f"Erreur API : {err}")
    else:
        categorie = data["categorie_risque"]
        score = data["score_risque"]
        COULEURS_RISQUE = {
            "faible": "#28a745",
            "moyen": "#ffc107",
            "eleve": "#fd7e14",
            "critique": "#dc3545",
        }
        couleur_risque = COULEURS_RISQUE.get(categorie, "#6c757d")
        st.divider()
        st.markdown("#### Profil de risque")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(
                f'<span style="background:{couleur_risque};color:white;'
                f"padding:4px 14px;border-radius:6px;font-weight:bold;"
                f'font-size:1.1em;">{categorie.upper()}</span>',
                unsafe_allow_html=True,
            )
            st.write("")
            st.metric("Score de risque", f"{score:.1%}")
        with col2:
            st.plotly_chart(
                jauge_risque(score, categorie),
                use_container_width=True,
            )
