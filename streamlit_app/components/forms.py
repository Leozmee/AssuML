"""
Formulaires réutilisables — AssuML Streamlit.

Chaque fonction retourne le dict de données prêt à envoyer à l'API,
ou None si le formulaire n'a pas été soumis.
"""

import streamlit as st
from datetime import date, timedelta
from typing import Optional

REGIONS_LABEL = {
    "northeast": "Northeast",
    "northwest": "Northwest",
    "southeast": "Southeast",
    "southwest": "Southwest",
}

REGIONS_ID_TO_STR = {1: "northeast", 2: "northwest", 3: "southeast", 4: "southwest"}
REGIONS_STR_TO_ID = {v: k for k, v in REGIONS_ID_TO_STR.items()}


def form_predict(key_prefix: str = "pred") -> Optional[dict]:
    """Formulaire de saisie pour les prédictions ML. Retourne le payload API ou None."""
    with st.form(key=f"{key_prefix}_form"):
        c1, c2 = st.columns(2)
        with c1:
            age = st.slider("Âge", 18, 90, 35)
            imc = st.slider("IMC", 10.0, 55.0, 25.0, step=0.1, format="%.1f")
            enfants = st.number_input("Enfants à charge", 0, 10, 0, step=1)
        with c2:
            sexe_label = st.radio("Sexe", ["Homme", "Femme"], horizontal=True)
            fumeur_label = st.radio("Fumeur", ["Non", "Oui"], horizontal=True)
            region_label = st.selectbox("Région", list(REGIONS_LABEL.values()))

        submitted = st.form_submit_button(
            "Scorer", use_container_width=True, type="primary"
        )

    if submitted:
        region_key = {v: k for k, v in REGIONS_LABEL.items()}[region_label]
        return {
            "age": age,
            "sexe": 0 if sexe_label == "Homme" else 1,
            "imc": imc,
            "enfants": enfants,
            "fumeur": 0 if fumeur_label == "Non" else 1,
            "region": region_key,
        }
    return None


def form_nouveau_client(key_prefix: str = "new_client") -> Optional[dict]:
    """Formulaire création client. Retourne le payload ClientCreate ou None."""
    with st.form(key=f"{key_prefix}_form"):
        c1, c2 = st.columns(2)
        with c1:
            age = st.slider("Âge", 18, 90, 35)
            imc = st.slider("IMC", 10.0, 55.0, 25.0, step=0.1, format="%.1f")
            enfants = st.number_input("Enfants à charge", 0, 10, 0, step=1)
        with c2:
            sexe_label = st.radio("Sexe", ["Homme", "Femme"], horizontal=True)
            fumeur_label = st.radio("Fumeur", ["Non", "Oui"], horizontal=True)
            region_label = st.selectbox("Région", list(REGIONS_LABEL.values()))

        email = st.text_input("Email (optionnel)", placeholder="client@exemple.com")
        telephone = st.text_input(
            "Téléphone (optionnel)", placeholder="+33 6 00 00 00 00"
        )

        submitted = st.form_submit_button(
            "Créer le client", use_container_width=True, type="primary"
        )

    if submitted:
        region_key = {v: k for k, v in REGIONS_LABEL.items()}[region_label]
        region_id = REGIONS_STR_TO_ID[region_key]
        return {
            "age": age,
            "sexe": "homme" if sexe_label == "Homme" else "femme",
            "imc": imc,
            "enfants": enfants,
            "fumeur": fumeur_label == "Oui",
            "region_id": region_id,
            "email": email if email else None,
            "telephone": telephone if telephone else None,
        }
    return None


def form_modifier_client(
    client: dict, key_prefix: str = "edit_client"
) -> Optional[dict]:
    """Formulaire modification client pré-rempli. Retourne le payload ClientUpdate."""
    region_str = REGIONS_ID_TO_STR.get(client.get("region_id", 1), "northeast")
    region_display = REGIONS_LABEL[region_str]

    with st.form(key=f"{key_prefix}_form"):
        c1, c2 = st.columns(2)
        with c1:
            age = st.slider("Âge", 18, 90, client.get("age", 35))
            imc = st.slider(
                "IMC",
                10.0,
                55.0,
                float(client.get("imc", 25.0)),
                step=0.1,
                format="%.1f",
            )
            enfants = st.number_input(
                "Enfants à charge", 0, 10, client.get("enfants", 0), step=1
            )
        with c2:
            sexe_options = ["Homme", "Femme"]
            sexe_idx = 0 if client.get("sexe") == "homme" else 1
            sexe_label = st.radio("Sexe", sexe_options, index=sexe_idx, horizontal=True)

            fumeur_options = ["Non", "Oui"]
            fumeur_idx = 1 if client.get("fumeur") else 0
            fumeur_label = st.radio(
                "Fumeur", fumeur_options, index=fumeur_idx, horizontal=True
            )

            region_options = list(REGIONS_LABEL.values())
            region_idx = region_options.index(region_display)
            region_label = st.selectbox("Région", region_options, index=region_idx)

        email = st.text_input("Email", value=client.get("email") or "")
        telephone = st.text_input("Téléphone", value=client.get("telephone") or "")

        submitted = st.form_submit_button(
            "Enregistrer", use_container_width=True, type="primary"
        )

    if submitted:
        region_key = {v: k for k, v in REGIONS_LABEL.items()}[region_label]
        region_id = REGIONS_STR_TO_ID[region_key]
        return {
            "age": age,
            "sexe": "homme" if sexe_label == "Homme" else "femme",
            "imc": imc,
            "enfants": enfants,
            "fumeur": fumeur_label == "Oui",
            "region_id": region_id,
            "email": email if email else None,
            "telephone": telephone if telephone else None,
        }
    return None


def form_nouveau_contrat(
    client_id: int, prime_suggestion: float = 0.0, key_prefix: str = "new_contrat"
) -> Optional[dict]:
    """Formulaire création contrat pour un client donné."""
    with st.form(key=f"{key_prefix}_form"):
        st.write(f"**Client ID** : {client_id}")
        prime = st.number_input(
            "Prime mensuelle (USD)",
            min_value=1.0,
            value=max(prime_suggestion, 50.0),
            step=10.0,
        )
        type_couverture = st.selectbox(
            "Type de couverture", ["basique", "standard", "premium", "famille"]
        )
        date_debut = st.date_input("Date de début", value=date.today())
        avec_fin = st.checkbox("Date de fin fixée")
        date_fin = None
        if avec_fin:
            date_fin = st.date_input(
                "Date de fin", value=date.today() + timedelta(days=365)
            )

        submitted = st.form_submit_button(
            "Créer le contrat", use_container_width=True, type="primary"
        )

    if submitted:
        payload = {
            "client_id": client_id,
            "prime_mensuelle": prime,
            "date_debut": date_debut.isoformat(),
            "type_couverture": type_couverture,
        }
        if date_fin:
            payload["date_fin"] = date_fin.isoformat()
        return payload
    return None
