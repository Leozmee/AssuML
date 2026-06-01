"""
Module 3 — Gestion CRUD.

Tableau paginé des clients avec actions par ligne (Voir / Modifier / Supprimer /
+Contrat / +Sinistre) selon les règles métier. Sous-sections Contrats et Sinistres.
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


# ── Initialisation session state ───────────────────────────────────────────────

def _init_state():
    defaults = {
        "client_action": None,
        "selected_client": None,
        "selected_contrat_id": None,
        "crud_page": 0,
        "crud_refresh": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ── Chargement données avec cache ──────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def charger_clients(_refresh: int):
    return api.get_all_clients()


@st.cache_data(ttl=30, show_spinner=False)
def charger_contrats(_refresh: int):
    return api.get_all_contrats()


def invalider_cache():
    st.session_state.crud_refresh += 1
    st.cache_data.clear()


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


# ── Chargement ─────────────────────────────────────────────────────────────────

with st.spinner("Chargement des clients..."):
    clients, err_clients = charger_clients(st.session_state.crud_refresh)
    contrats, err_contrats = charger_contrats(st.session_state.crud_refresh)

if err_clients:
    st.error(f"Impossible de charger les clients : {err_clients}")
    st.stop()

contrats = contrats or []

# Index contrats par client_id (dernier contrat actif ou premier trouvé)
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
        st.session_state.client_action = "nouveau"
        st.session_state.selected_client = None

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

# Pagination
total = len(clients_filtres)
nb_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
page = min(st.session_state.crud_page, nb_pages - 1)

st.caption(f"{total} client(s) trouvé(s) — page {page + 1}/{nb_pages}")

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

    # Colonnes d'actions
    with row[7]:
        a1, a2, a3, a4, a5 = st.columns(5)

        # Voir
        if a1.button("Voir", key=f"voir_{cid}", help="Détails"):
            st.session_state.selected_client = client
            st.session_state.client_action = "voir"

        # Modifier
        if a2.button("Éditer", key=f"edit_{cid}", help="Modifier"):
            st.session_state.selected_client = client
            st.session_state.client_action = "modifier"

        # Supprimer
        if a3.button("Suppr.", key=f"del_{cid}", help="Supprimer"):
            st.session_state.selected_client = client
            st.session_state.client_action = "supprimer"

        # +Contrat — désactivé si contrat déjà existant
        if contrat is not None:
            a4.markdown(_BADGE_CONTRAT_EXISTANT, unsafe_allow_html=True)
        else:
            if a4.button("📄+", key=f"contrat_{cid}", help="Nouveau contrat"):
                st.session_state.selected_client = client
                st.session_state.client_action = "contrat"

        # +Sinistre — règles métier
        if contrat is None:
            a5.markdown(_BADGE_SINISTRE_IMPOSSIBLE, unsafe_allow_html=True)
        elif statut_contrat != "actif":
            a5.markdown(
                _badge_sinistre_bloque(statut_contrat), unsafe_allow_html=True
            )
        else:
            if a5.button("⚠️+", key=f"sinistre_{cid}", help="Déclarer un sinistre"):
                st.session_state.selected_client = client
                st.session_state.selected_contrat_id = contrat["contrat_id"]
                st.session_state.client_action = "sinistre"

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

# ── Panneau d'action ──────────────────────────────────────────────────────────

action = st.session_state.get("client_action")
selected = st.session_state.get("selected_client")

if action:
    st.divider()

    # ── Nouveau client ────────────────────────────────────────────────────────
    if action == "nouveau":
        st.subheader("Nouveau client")
        payload = form_nouveau_client(key_prefix="new_main")
        if payload is not None:
            data, err = api.create_client(payload)
            if err:
                st.error(f"Erreur création : {err}")
            else:
                st.success(f"Client créé — ID {data['client_id']}")
                invalider_cache()
                st.session_state.client_action = None
                st.rerun()
        if st.button("Annuler", key="cancel_new"):
            st.session_state.client_action = None
            st.rerun()

    # ── Voir client ────────────────────────────────────────────────────────────
    elif action == "voir" and selected:
        st.subheader(f"Client #{selected['client_id']}")
        col1, col2 = st.columns(2)
        col1.write(f"**Âge** : {selected['age']}")
        col1.write(f"**Sexe** : {selected['sexe'].capitalize()}")
        col1.write(f"**IMC** : {selected['imc']:.1f}")
        col1.write(f"**Enfants** : {selected['enfants']}")
        col2.write(f"**Fumeur** : {'Oui' if selected['fumeur'] else 'Non'}")
        col2.write(f"**Région** : {REGIONS_ID_TO_STR.get(selected['region_id'], '?')}")
        col2.write(f"**Email** : {selected.get('email') or '—'}")
        col2.write(f"**Téléphone** : {selected.get('telephone') or '—'}")
        contrat_client = contrats_by_client.get(selected["client_id"])
        statut_c = contrat_client["statut"] if contrat_client else None
        st.markdown(
            f"**Contrat** : {badge_statut_contrat(statut_c)}",
            unsafe_allow_html=True,
        )
        if st.button("Fermer", key="close_voir"):
            st.session_state.client_action = None
            st.rerun()

    # ── Modifier client ────────────────────────────────────────────────────────
    elif action == "modifier" and selected:
        st.subheader(f"Modifier client #{selected['client_id']}")
        kp = f"edit_{selected['client_id']}"
        payload = form_modifier_client(selected, key_prefix=kp)
        if payload is not None:
            data, err = api.update_client(selected["client_id"], payload)
            if err:
                st.error(f"Erreur modification : {err}")
            else:
                st.success("Client mis à jour.")
                invalider_cache()
                st.session_state.client_action = None
                st.rerun()
        if st.button("Annuler", key="cancel_edit"):
            st.session_state.client_action = None
            st.rerun()

    # ── Supprimer client ──────────────────────────────────────────────────────
    elif action == "supprimer" and selected:
        st.subheader(f"Supprimer client #{selected['client_id']}")
        st.warning(
            f"Cette action désactivera définitivement le client "
            f"**#{selected['client_id']}** (soft delete). "
            f"Le client ne pourra plus être récupéré via l'API.",
            icon="⚠️",
        )
        col_confirm, col_cancel = st.columns(2)
        if col_confirm.button(
            "Confirmer la suppression", type="primary", key="confirm_del"
        ):
            data, err = api.delete_client(selected["client_id"])
            if err:
                st.error(f"Erreur suppression : {err}")
            else:
                st.success(f"Client #{selected['client_id']} désactivé.")
                invalider_cache()
                st.session_state.client_action = None
                st.session_state.selected_client = None
                st.rerun()
        if col_cancel.button("Annuler", key="cancel_del"):
            st.session_state.client_action = None
            st.rerun()

    # ── Nouveau contrat ────────────────────────────────────────────────────────
    elif action == "contrat" and selected:
        st.subheader(f"Nouveau contrat pour client #{selected['client_id']}")
        kp = f"contrat_{selected['client_id']}"
        payload = form_nouveau_contrat(selected["client_id"], key_prefix=kp)
        if payload is not None:
            data, err = api.create_contrat(payload)
            if err:
                st.error(f"Erreur création contrat : {err}")
            else:
                st.success(f"Contrat créé — ID {data['contrat_id']}")
                invalider_cache()
                st.session_state.client_action = None
                st.rerun()
        if st.button("Annuler", key="cancel_contrat"):
            st.session_state.client_action = None
            st.rerun()

    # ── Nouveau sinistre ──────────────────────────────────────────────────────
    elif action == "sinistre" and selected:
        contrat_id = st.session_state.get("selected_contrat_id")
        st.subheader(f"Déclarer un sinistre — Contrat #{contrat_id}")
        if contrat_id:
            kp = f"sinistre_{contrat_id}"
            payload = form_nouveau_sinistre(contrat_id, key_prefix=kp)
            if payload is not None:
                data, err = api.create_sinistre(payload)
                if err:
                    st.error(f"Erreur déclaration sinistre : {err}")
                else:
                    st.success(f"Sinistre déclaré — ID {data['sinistre_id']}")
                    invalider_cache()
                    st.session_state.client_action = None
                    st.rerun()
        if st.button("Annuler", key="cancel_sinistre"):
            st.session_state.client_action = None
            st.rerun()

# ── Séparateur ────────────────────────────────────────────────────────────────

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
                data, err = api.update_sinistre_statut(sinistre_id_mod, statut_sinistre)
                if err:
                    st.error(f"Erreur : {err}")
                else:
                    st.success(f"Sinistre #{sinistre_id_mod} → {statut_sinistre}")
                    invalider_cache()
                    st.rerun()
