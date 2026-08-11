"""
Module 3 — Gestion CRUD.

Tableau paginé des clients avec actions par ligne via popups @st.dialog.
Sous-section Contrats dans un expander.
"""

import streamlit as st

from utils import api_client as api
from components.forms import (
    form_nouveau_client,
    form_modifier_client,
    form_nouveau_contrat,
)
from components.metrics import badge_statut_contrat, badge_categorie_risque

st.set_page_config(page_title="CRUD — AssuML", page_icon="👥", layout="wide")
st.title("👥 Gestion des clients")

REGIONS_ID_TO_STR = {1: "Northeast", 2: "Northwest", 3: "Southeast", 4: "Southwest"}
REGIONS_ID_TO_API = {1: "northeast", 2: "northwest", 3: "southeast", 4: "southwest"}
PAGE_SIZE = 20

# ── HTML badges inline ────────────────────────────────────────────────────────

_BADGE_CONTRAT_EXISTANT = (
    '<span title="Contrat existant" '
    'style="color:#999;text-decoration:line-through;font-size:0.8em;">'
    "📄 Contrat</span>"
)


def invalider_cache():
    st.cache_data.clear()


# ── Dialogs (popups modaux) ────────────────────────────────────────────────────


@st.dialog("Nouveau client", width="large")
def dialog_nouveau_client():
    payload = form_nouveau_client(key_prefix="dlg_new")
    if payload is not None:
        data, err = api.create_client(payload)
        if err:
            st.error(f"Erreur création : {err}")
        else:
            st.success(f"Client créé — ID {data['client_id']}")
            invalider_cache()
            st.rerun()


@st.dialog("Détails client")
def dialog_voir_client(client: dict, contrat):
    col1, col2 = st.columns(2)
    col1.write(f"**Âge** : {client['age']}")
    col1.write(f"**Sexe** : {client['sexe'].capitalize()}")
    col1.write(f"**IMC** : {client['imc']:.1f}")
    col1.write(f"**Enfants** : {client['enfants']}")
    col2.write(f"**Fumeur** : {'Oui' if client['fumeur'] else 'Non'}")
    col2.write(f"**Région** : {REGIONS_ID_TO_STR.get(client['region_id'], '?')}")
    col2.write(f"**Email** : {client.get('email') or '—'}")
    col2.write(f"**Téléphone** : {client.get('telephone') or '—'}")
    statut_c = contrat["statut"] if contrat else None
    st.markdown(
        f"**Contrat** : {badge_statut_contrat(statut_c)}",
        unsafe_allow_html=True,
    )


@st.dialog("Modifier client", width="large")
def dialog_modifier_client(client: dict):
    kp = f"dlg_edit_{client['client_id']}"
    payload = form_modifier_client(client, key_prefix=kp)
    if payload is not None:
        data, err = api.update_client(client["client_id"], payload)
        if err:
            st.error(f"Erreur modification : {err}")
        else:
            st.success("Client mis à jour.")
            invalider_cache()
            st.rerun()


@st.dialog("Supprimer le client")
def dialog_supprimer_client(client: dict):
    st.warning(
        f"Désactiver définitivement le client **#{client['client_id']}** "
        f"(soft delete — données conservées en base) ?",
        icon="⚠️",
    )
    col1, col2 = st.columns(2)
    if col1.button("Confirmer", type="primary", use_container_width=True):
        data, err = api.delete_client(client["client_id"])
        if err:
            st.error(f"Erreur : {err}")
        else:
            st.success(f"Client #{client['client_id']} désactivé.")
            invalider_cache()
            st.rerun()
    if col2.button("Annuler", use_container_width=True):
        st.rerun()


@st.dialog("Scoring — Prédiction ML", width="large")
def dialog_scorer_client(client: dict):
    from business.scoring import COEFFICIENTS

    st.caption(
        f"Client #{client['client_id']} · {client['sexe'].capitalize()}, {client['age']} ans"
    )

    payload = {
        "age": client["age"],
        "sexe": 1 if client["sexe"] == "femme" else 0,
        "imc": float(client["imc"]),
        "enfants": client["enfants"],
        "fumeur": 1 if client["fumeur"] else 0,
        "region": REGIONS_ID_TO_API.get(client["region_id"], "northeast"),
        "client_id": client["client_id"],
    }

    with st.spinner("Calcul en cours..."):
        data, err = api.predict_complet(payload)

    if err:
        st.error(f"Erreur : {err}")
        return

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

    with col1:
        st.markdown("#### Estimation ML du coût médical")
        st.metric("Coût annuel prédit", f"${cout:,.2f}")
        st.metric("Coût mensuel prédit", f"${cout_mensuel:,.2f}")

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

    with col3:
        st.markdown("#### Prime à facturer au client")
        st.metric(
            "Prime annuelle",
            f"${prime_annuelle:,.2f}",
            delta=f"+${marge_annuelle:,.2f} marge",
        )
        st.metric("Prime mensuelle", f"${prime_mensuelle:,.2f}")
        st.metric("Marge annuelle", f"${marge_annuelle:,.2f}")

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

    if data.get("deja_existante"):
        st.info(
            f"Données inchangées — prédiction existante retournée (ID : {data['prediction_id']})",
            icon="ℹ️",
        )
    elif data.get("prediction_id"):
        st.success(f"Prédiction persistée en base — ID : {data['prediction_id']}")


@st.dialog("Résilier le contrat")
def dialog_resilier_contrat(contrat: dict):
    st.warning(
        f"Résilier définitivement le contrat **#{contrat['contrat_id']}** "
        f"(prime : ${contrat['prime_mensuelle']:,.2f}/mois · {contrat['type_couverture']}) ?",
        icon="⚠️",
    )
    st.caption("Le statut passera à « Résilié » — le contrat reste visible en base.")
    col1, col2 = st.columns(2)
    if col1.button(
        "Confirmer la résiliation", type="primary", use_container_width=True
    ):
        data, err = api.update_contrat_statut(contrat["contrat_id"], "resilie")
        if err:
            st.error(f"Erreur : {err}")
        else:
            st.success(f"Contrat #{contrat['contrat_id']} résilié.")
            invalider_cache()
            st.rerun()
    if col2.button("Annuler", use_container_width=True):
        st.rerun()


@st.dialog("Nouveau contrat", width="large")
def dialog_nouveau_contrat(client_id: int, client: dict, prime_annuelle):
    state_prime_key = f"prime_contrat_{client_id}"
    state_version_key = f"prime_contrat_v_{client_id}"

    # Détermine la prime mensuelle suggérée
    if prime_annuelle is not None:
        prime_suggestion = prime_annuelle / 12
    elif state_prime_key in st.session_state:
        prime_suggestion = st.session_state[state_prime_key]
    else:
        prime_suggestion = 0.0

    # Bannière prime ML ou bouton de prédiction
    if prime_suggestion > 0.0:
        st.info(
            f"Prime recommandée par le modèle ML : **${prime_suggestion:,.2f} / mois**",
            icon="🤖",
        )
    else:
        st.warning("Aucune prédiction disponible pour ce client.", icon="⚠️")
        if st.button(
            "⚡ Calculer la prime via le modèle ML",
            type="secondary",
            use_container_width=True,
            key=f"btn_pred_contrat_{client_id}",
        ):
            payload_pred = {
                "age": client["age"],
                "sexe": 1 if client["sexe"] == "femme" else 0,
                "imc": float(client["imc"]),
                "enfants": client["enfants"],
                "fumeur": 1 if client["fumeur"] else 0,
                "region": REGIONS_ID_TO_API.get(client["region_id"], "northeast"),
                "client_id": client_id,
            }
            with st.spinner("Calcul en cours..."):
                pred_data, pred_err = api.predict_complet(payload_pred)
            if pred_err:
                st.error(f"Erreur prédiction : {pred_err}")
            else:
                st.session_state[state_prime_key] = pred_data["prime"] / 12
                st.session_state[state_version_key] = (
                    st.session_state.get(state_version_key, 0) + 1
                )
                invalider_cache()

    # Formulaire contrat — clé versionnée pour forcer le rechargement après prédiction
    version = st.session_state.get(state_version_key, 0)
    payload = form_nouveau_contrat(
        client_id,
        prime_suggestion=prime_suggestion,
        key_prefix=f"dlg_contrat_{client_id}_v{version}",
    )
    if payload is not None:
        data, err = api.create_contrat(payload)
        if err:
            st.error(f"Erreur création contrat : {err}")
        else:
            st.success(f"Contrat créé — ID {data['contrat_id']}")
            st.session_state.pop(state_prime_key, None)
            st.session_state.pop(state_version_key, None)
            invalider_cache()
            st.rerun()


# ── Chargement données avec cache ──────────────────────────────────────────────


@st.cache_data(ttl=30, show_spinner=False)
def charger_clients(_refresh: int):
    return api.get_all_clients()


@st.cache_data(ttl=30, show_spinner=False)
def charger_contrats(_refresh: int):
    return api.get_all_contrats()


@st.cache_data(ttl=30, show_spinner=False)
def charger_predictions(_refresh: int):
    return api.get_dernieres_predictions()


if "crud_refresh" not in st.session_state:
    st.session_state.crud_refresh = 0
if "crud_page" not in st.session_state:
    st.session_state.crud_page = 0

with st.spinner("Chargement des clients..."):
    clients, err_clients = charger_clients(st.session_state.crud_refresh)
    contrats, err_contrats = charger_contrats(st.session_state.crud_refresh)
    predictions, _ = charger_predictions(st.session_state.crud_refresh)

if err_clients:
    st.error(f"Impossible de charger les clients : {err_clients}")
    st.stop()

contrats = contrats or []
predictions = predictions or []

contrats_by_client = {}
for c in contrats:
    cid = c["client_id"]
    existing = contrats_by_client.get(cid)
    if existing is None or c["statut"] == "actif":
        contrats_by_client[cid] = c

predictions_by_client = {p["client_id"]: p for p in predictions}

# ── Barre de recherche + bouton nouveau ───────────────────────────────────────

col_search, col_btn = st.columns([4, 1])
with col_search:
    recherche = st.text_input(
        "Rechercher un client",
        placeholder="ID, email, région...",
        label_visibility="collapsed",
    )
with col_btn:
    if st.button("+ Nouveau client", use_container_width=True, type="primary"):
        dialog_nouveau_client()

# ── Filtrage ───────────────────────────────────────────────────────────────────

clients_filtres = clients or []
if recherche:
    q = recherche.lower()
    clients_filtres = [
        c
        for c in clients_filtres
        if q in str(c["client_id"])
        or q in (c.get("email") or "").lower()
        or q in REGIONS_ID_TO_STR.get(c["region_id"], "").lower()
        or q in c["sexe"].lower()
    ]

total = len(clients_filtres)
nb_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
page = min(st.session_state.crud_page, nb_pages - 1)

st.caption(f"{total} client(s) — page {page + 1}/{nb_pages}")

clients_page = clients_filtres[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]  # noqa: E203

# ── En-tête du tableau ────────────────────────────────────────────────────────

hdr = st.columns([1, 1, 2, 2, 2, 2, 2, 2, 5])
for col, label in zip(
    hdr,
    [
        "ID",
        "Âge",
        "Sexe",
        "IMC",
        "Fumeur",
        "Région",
        "Risque",
        "Statut contrat",
        "Actions",
    ],
):
    col.markdown(f"**{label}**")
st.divider()

# ── Lignes du tableau ─────────────────────────────────────────────────────────

for client in clients_page:
    cid = client["client_id"]
    contrat = contrats_by_client.get(cid)
    statut_contrat = contrat["statut"] if contrat else None

    pred = predictions_by_client.get(cid)
    categorie_risque = pred["categorie_risque"] if pred else None

    row = st.columns([1, 1, 2, 2, 2, 2, 2, 2, 5])
    row[0].write(cid)
    row[1].write(client["age"])
    row[2].write(client["sexe"].capitalize())
    row[3].write(f"{client['imc']:.1f}")
    row[4].write("Oui" if client["fumeur"] else "Non")
    row[5].write(REGIONS_ID_TO_STR.get(client["region_id"], "?"))
    row[6].markdown(badge_categorie_risque(categorie_risque), unsafe_allow_html=True)
    row[7].markdown(badge_statut_contrat(statut_contrat), unsafe_allow_html=True)

    with row[8]:
        a1, a2, a3, a4, a5 = st.columns(5)

        if a1.button("Voir", key=f"voir_{cid}"):
            dialog_voir_client(client, contrat)

        if a2.button("Éditer", key=f"edit_{cid}"):
            dialog_modifier_client(client)

        if a3.button("Suppr.", key=f"del_{cid}"):
            dialog_supprimer_client(client)

        if contrat is not None:
            if contrat["statut"] == "actif":
                if a4.button("📄✕", key=f"resilier_{cid}", help="Résilier le contrat"):
                    dialog_resilier_contrat(contrat)
            else:
                a4.markdown(
                    badge_statut_contrat(contrat["statut"]), unsafe_allow_html=True
                )
        else:
            if a4.button("📄+", key=f"contrat_{cid}", help="Nouveau contrat"):
                prime_annuelle = pred["prime"] if pred else None
                dialog_nouveau_contrat(cid, client, prime_annuelle)

        if a5.button("⚡", key=f"score_{cid}", help="Lancer le scoring ML"):
            dialog_scorer_client(client)

# ── Navigation pages ─────────────────────────────────────────────────────────

st.divider()
nav_l, nav_info, nav_r = st.columns([1, 3, 1])
if nav_l.button("← Précédent", disabled=(page == 0)):
    st.session_state.crud_page = max(0, page - 1)
    st.rerun()
nav_html = f"<div style='text-align:center'>Page {page + 1} / {nb_pages}</div>"
nav_info.markdown(nav_html, unsafe_allow_html=True)
if nav_r.button("Suivant →", disabled=(page >= nb_pages - 1)):
    st.session_state.crud_page = page + 1
    st.rerun()

st.divider()

# ── Sous-section Contrats ─────────────────────────────────────────────────────

with st.expander("📋 Tous les contrats", expanded=False):
    if err_contrats:
        st.error(f"Impossible de charger les contrats : {err_contrats}")
    elif not contrats:
        st.info("Aucun contrat enregistré.")
    else:
        # En-tête
        ch = st.columns([1, 1, 2, 2, 2, 2, 2])
        for col, label in zip(
            ch,
            ["ID", "Client", "Statut", "Prime/mois", "Couverture", "Début", "Actions"],
        ):
            col.markdown(f"**{label}**")
        st.divider()

        for c in contrats:
            crow = st.columns([1, 1, 2, 2, 2, 2, 2])
            crow[0].write(c["contrat_id"])
            crow[1].write(c["client_id"])
            crow[2].markdown(badge_statut_contrat(c["statut"]), unsafe_allow_html=True)
            crow[3].write(f"${c['prime_mensuelle']:,.2f}")
            crow[4].write(c["type_couverture"].capitalize())
            crow[5].write(str(c["date_debut"])[:10])
            with crow[6]:
                if c["statut"] == "actif":
                    if st.button(
                        "Résilier",
                        key=f"res_exp_{c['contrat_id']}",
                        type="primary",
                        use_container_width=True,
                    ):
                        dialog_resilier_contrat(c)
                else:
                    st.caption("—")
        st.divider()

        st.markdown("**Modifier le statut d'un contrat**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            contrat_id_mod = st.number_input(
                "ID contrat", min_value=1, value=1, step=1, key="mod_contrat_id"
            )
        with col2:
            nouveau_statut = st.selectbox(
                "Nouveau statut",
                ["actif", "resilie", "expire", "suspendu"],
                key="mod_contrat_statut",
            )
        with col3:
            st.write("")
            st.write("")
            if st.button("Modifier", key="btn_mod_contrat"):
                data, err = api.update_contrat_statut(contrat_id_mod, nouveau_statut)
                if err:
                    st.error(f"Erreur : {err}")
                else:
                    st.success(f"Contrat #{contrat_id_mod} → {nouveau_statut}")
                    invalider_cache()
                    st.rerun()
