"""
Module 3 — Gestion CRUD.

Tableau paginé des clients avec actions par ligne via popups @st.dialog.
Sous-sections Contrats et Sinistres dans des expanders.
"""

import streamlit as st

from utils import api_client as api
from components.forms import (
    form_nouveau_client,
    form_modifier_client,
    form_nouveau_contrat,
    form_nouveau_sinistre,
)
from components.metrics import badge_statut_contrat

st.set_page_config(page_title="CRUD — AssuML", page_icon="👥", layout="wide")
st.title("👥 Gestion des clients")

REGIONS_ID_TO_STR = {1: "Northeast", 2: "Northwest", 3: "Southeast", 4: "Southwest"}
PAGE_SIZE = 20

# ── HTML badges inline ────────────────────────────────────────────────────────

_BADGE_CONTRAT_EXISTANT = (
    '<span title="Contrat existant" '
    'style="color:#999;text-decoration:line-through;font-size:0.8em;">'
    "📄 Contrat</span>"
)
_BADGE_SINISTRE_IMPOSSIBLE = (
    '<span title="Sinistre impossible — pas de contrat" '
    'style="color:#999;font-size:0.8em;">⛔ Sinistre</span>'
)


def _badge_sinistre_bloque(statut: str) -> str:
    return (
        f'<span title="Sinistre bloqué — contrat {statut}" '
        'style="color:#fd7e14;font-size:0.8em;">🔒 Bloqué</span>'
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
    col2.write(
        f"**Région** : {REGIONS_ID_TO_STR.get(client['region_id'], '?')}"
    )
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


@st.dialog("Nouveau contrat", width="large")
def dialog_nouveau_contrat(client_id: int):
    payload = form_nouveau_contrat(client_id, key_prefix=f"dlg_contrat_{client_id}")
    if payload is not None:
        data, err = api.create_contrat(payload)
        if err:
            st.error(f"Erreur création contrat : {err}")
        else:
            st.success(f"Contrat créé — ID {data['contrat_id']}")
            invalider_cache()
            st.rerun()


@st.dialog("Déclarer un sinistre", width="large")
def dialog_nouveau_sinistre(contrat_id: int):
    payload = form_nouveau_sinistre(
        contrat_id, key_prefix=f"dlg_sinistre_{contrat_id}"
    )
    if payload is not None:
        data, err = api.create_sinistre(payload)
        if err:
            st.error(f"Erreur déclaration sinistre : {err}")
        else:
            st.success(f"Sinistre déclaré — ID {data['sinistre_id']}")
            invalider_cache()
            st.rerun()


# ── Chargement données avec cache ──────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def charger_clients(_refresh: int):
    return api.get_all_clients()


@st.cache_data(ttl=30, show_spinner=False)
def charger_contrats(_refresh: int):
    return api.get_all_contrats()


if "crud_refresh" not in st.session_state:
    st.session_state.crud_refresh = 0
if "crud_page" not in st.session_state:
    st.session_state.crud_page = 0

with st.spinner("Chargement des clients..."):
    clients, err_clients = charger_clients(st.session_state.crud_refresh)
    contrats, err_contrats = charger_contrats(st.session_state.crud_refresh)

if err_clients:
    st.error(f"Impossible de charger les clients : {err_clients}")
    st.stop()

contrats = contrats or []

contrats_by_client = {}
for c in contrats:
    cid = c["client_id"]
    existing = contrats_by_client.get(cid)
    if existing is None or c["statut"] == "actif":
        contrats_by_client[cid] = c

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
        c for c in clients_filtres
        if q in str(c["client_id"])
        or q in (c.get("email") or "").lower()
        or q in REGIONS_ID_TO_STR.get(c["region_id"], "").lower()
        or q in c["sexe"].lower()
    ]

total = len(clients_filtres)
nb_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
page = min(st.session_state.crud_page, nb_pages - 1)

st.caption(f"{total} client(s) — page {page + 1}/{nb_pages}")

clients_page = clients_filtres[page * PAGE_SIZE: (page + 1) * PAGE_SIZE]

# ── En-tête du tableau ────────────────────────────────────────────────────────

hdr = st.columns([1, 1, 2, 2, 2, 2, 2, 5])
for col, label in zip(
    hdr,
    ["ID", "Âge", "Sexe", "IMC", "Fumeur", "Région", "Statut contrat", "Actions"],
):
    col.markdown(f"**{label}**")
st.divider()

# ── Lignes du tableau ─────────────────────────────────────────────────────────

for client in clients_page:
    cid = client["client_id"]
    contrat = contrats_by_client.get(cid)
    statut_contrat = contrat["statut"] if contrat else None

    row = st.columns([1, 1, 2, 2, 2, 2, 2, 5])
    row[0].write(cid)
    row[1].write(client["age"])
    row[2].write(client["sexe"].capitalize())
    row[3].write(f"{client['imc']:.1f}")
    row[4].write("Oui" if client["fumeur"] else "Non")
    row[5].write(REGIONS_ID_TO_STR.get(client["region_id"], "?"))
    row[6].markdown(badge_statut_contrat(statut_contrat), unsafe_allow_html=True)

    with row[7]:
        a1, a2, a3, a4, a5 = st.columns(5)

        if a1.button("Voir", key=f"voir_{cid}"):
            dialog_voir_client(client, contrat)

        if a2.button("Éditer", key=f"edit_{cid}"):
            dialog_modifier_client(client)

        if a3.button("Suppr.", key=f"del_{cid}"):
            dialog_supprimer_client(client)

        if contrat is not None:
            a4.markdown(_BADGE_CONTRAT_EXISTANT, unsafe_allow_html=True)
        else:
            if a4.button("📄+", key=f"contrat_{cid}", help="Nouveau contrat"):
                dialog_nouveau_contrat(cid)

        if contrat is None:
            a5.markdown(_BADGE_SINISTRE_IMPOSSIBLE, unsafe_allow_html=True)
        elif statut_contrat != "actif":
            a5.markdown(
                _badge_sinistre_bloque(statut_contrat), unsafe_allow_html=True
            )
        else:
            if a5.button("⚠️+", key=f"sinistre_{cid}", help="Déclarer un sinistre"):
                dialog_nouveau_sinistre(contrat["contrat_id"])

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
        from components.tables import df_contrats as make_df_contrats

        df = make_df_contrats(contrats)
        st.dataframe(df, use_container_width=True, hide_index=True)

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

# ── Sous-section Sinistres ────────────────────────────────────────────────────

with st.expander("⚠️ Tous les sinistres", expanded=False):
    sinistres, err_sinistres = api.get_all_sinistres()
    if err_sinistres:
        st.error(f"Impossible de charger les sinistres : {err_sinistres}")
    elif not sinistres:
        st.info("Aucun sinistre enregistré.")
    else:
        from components.tables import df_sinistres as make_df_sinistres

        df = make_df_sinistres(sinistres)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("**Modifier le statut d'un sinistre**")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            sinistre_id_mod = st.number_input(
                "ID sinistre", min_value=1, value=1, step=1, key="mod_sinistre_id"
            )
        with col2:
            statut_sinistre = st.selectbox(
                "Nouveau statut",
                ["en_cours", "accepte", "refuse", "rembourse"],
                key="mod_sinistre_statut",
            )
        with col3:
            st.write("")
            st.write("")
            if st.button("Modifier", key="btn_mod_sinistre"):
                data, err = api.update_sinistre_statut(
                    sinistre_id_mod, statut_sinistre
                )
                if err:
                    st.error(f"Erreur : {err}")
                else:
                    st.success(f"Sinistre #{sinistre_id_mod} → {statut_sinistre}")
                    invalider_cache()
                    st.rerun()
