"""
AssuML — Application Streamlit de scoring assurantiel.

Point d'entrée principal. Configuration de la page et navigation.
"""

import streamlit as st

st.set_page_config(
    page_title="AssuML — Scoring Assurance",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("AssuML — Système de Souscription Assurance IA")
st.markdown(
    """
    Bienvenue sur la plateforme de scoring assurantiel **AssuML**.

    Naviguez via la barre latérale :

    | Module | Description |
    |--------|-------------|
    | 🎯 Scoring | Prédiction de coût, risque et prime à partir d'un profil |
    | 📊 Analytics | KPIs du portefeuille et tableau de bord Big Data |
    | 👥 CRUD | Gestion des clients, contrats et sinistres |
    | 📈 Monitoring | Santé API, métriques ML et détection de drift |
    | 📰 Actualités | Articles santé et données météo régionales |
    """
)

st.info(
    "Assurez-vous que l'API FastAPI tourne sur le port 8000 : "
    "`uvicorn api.main:app --reload --port 8000`",
    icon="ℹ️",
)
