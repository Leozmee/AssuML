"""
Composants d'affichage de métriques KPI — AssuML Streamlit.
"""

import streamlit as st


def afficher_kpis(kpis: dict) -> None:
    """Affiche les KPIs globaux en colonnes."""
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        label="Clients actifs",
        value=f"{kpis.get('nb_clients_actifs', 0):,}",
    )
    c2.metric(
        label="Contrats actifs",
        value=f"{kpis.get('nb_contrats_actifs', 0):,}",
    )

    cout_moyen = kpis.get("cout_moyen_predit")
    c3.metric(
        label="Coût moyen prédit",
        value=f"${cout_moyen:,.0f}" if cout_moyen is not None else "N/A",
    )

    rep = kpis.get("repartition_risque", {})
    total_pred = sum(rep.values())
    c4.metric(
        label="Prédictions totales",
        value=f"{total_pred:,}",
    )


def badge_decision(decision: str) -> str:
    """Retourne le HTML d'un badge coloré selon la décision."""
    couleurs = {
        "accepter": ("#28a745", "white"),
        "examiner": ("#fd7e14", "white"),
        "refuser": ("#dc3545", "white"),
    }
    bg, fg = couleurs.get(decision, ("#6c757d", "white"))
    label = decision.upper()
    return (
        f'<span style="background:{bg};color:{fg};padding:4px 12px;'
        f'border-radius:6px;font-weight:bold;font-size:1.1em;">{label}</span>'
    )


def badge_categorie_risque(categorie) -> str:
    """Retourne le HTML d'un badge de catégorie de risque ML."""
    if categorie is None:
        return '<span style="color:#6c757d;font-size:0.85em;">Aucune prédiction</span>'
    mapping = {
        "faible": ("#28a745", "Faible"),
        "moyen": ("#ffc107", "Moyen"),
        "eleve": ("#fd7e14", "Élevé"),
        "critique": ("#dc3545", "Critique"),
    }
    bg, libelle = mapping.get(categorie, ("#6c757d", categorie.capitalize()))
    color = "white" if categorie != "moyen" else "#212529"
    return (
        f'<span style="background:{bg};color:{color};padding:2px 8px;'
        f'border-radius:4px;font-size:0.85em;font-weight:bold;">{libelle}</span>'
    )


def badge_statut_contrat(statut) -> str:
    """Retourne le HTML d'un badge de statut contrat."""
    if statut is None:
        return '<span style="color:#6c757d;">⚫ Aucun</span>'
    mapping = {
        "actif": ("🟢", "#28a745", "Actif"),
        "suspendu": ("🟠", "#fd7e14", "Suspendu"),
        "resilie": ("🔴", "#dc3545", "Résilié"),
        "expire": ("⚫", "#6c757d", "Expiré"),
    }
    emoji, couleur, libelle = mapping.get(statut, ("⚪", "#888", statut.capitalize()))
    return f'<span style="color:{couleur};font-weight:bold;">{emoji} {libelle}</span>'


def afficher_metriques_modele(meta: dict) -> None:
    """Affiche les métriques des deux modèles ML côte à côte."""
    reg = meta.get("regression", {})
    clf = meta.get("classification", {})
    reg_m = reg.get("metriques_test", {})
    clf_m = clf.get("metriques_test", {})

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Régression (coût)")
        algo_r = reg.get("algorithme", "?")
        date_r = reg.get("date_entrainement", "?")
        st.caption(f"Algorithme : {algo_r} — {date_r}")
        m1, m2, m3 = st.columns(3)
        m1.metric("R²", f"{reg_m.get('r2', 0):.4f}")
        m2.metric("MAE", f"${reg_m.get('mae', 0):,.0f}")
        m3.metric("RMSE", f"${reg_m.get('rmse', 0):,.0f}")
        cv = reg.get("metriques_cv", {})
        st.caption(f"CV R² : {cv.get('r2_mean', 0):.4f} ± {cv.get('r2_std', 0):.4f}")

    with col2:
        st.subheader("Classification (risque)")
        algo_c = clf.get("algorithme", "?")
        date_c = clf.get("date_entrainement", "?")
        st.caption(f"Algorithme : {algo_c} — {date_c}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Accuracy", f"{clf_m.get('accuracy', 0):.4f}")
        m2.metric("F1 macro", f"{clf_m.get('f1_macro', 0):.4f}")
        m3.metric("Précision", f"{clf_m.get('precision_macro', 0):.4f}")
        m4.metric("Rappel", f"{clf_m.get('recall_macro', 0):.4f}")
        cv = clf.get("metriques_cv", {})
        mean = cv.get("accuracy_mean", 0)
        std = cv.get("accuracy_std", 0)
        st.caption(f"CV Accuracy : {mean:.4f} ± {std:.4f}")
