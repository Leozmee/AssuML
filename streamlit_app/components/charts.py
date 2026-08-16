"""
Composants graphiques réutilisables — Plotly pour AssuML Streamlit.
"""

import plotly.graph_objects as go


COULEUR_DECISION = {
    "accepter": "#28a745",
    "examiner": "#fd7e14",
    "refuser": "#dc3545",
}

COULEUR_RISQUE = {
    "faible": "#28a745",
    "moyen": "#ffc107",
    "eleve": "#fd7e14",
    "critique": "#dc3545",
}


def jauge_cout(cout: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=cout,
            title={"text": "Coût médical prédit (USD)", "font": {"size": 14}},
            number={"prefix": "$", "valueformat": ",.0f"},
            gauge={
                "axis": {"range": [0, 60000], "tickformat": "$,.0f"},
                "bar": {"color": "#4e79a7"},
                "steps": [
                    {"range": [0, 10000], "color": "#d4edda"},
                    {"range": [10000, 25000], "color": "#fff3cd"},
                    {"range": [25000, 60000], "color": "#f8d7da"},
                ],
                "threshold": {
                    "line": {"color": "#333", "width": 2},
                    "thickness": 0.75,
                    "value": cout,
                },
            },
        )
    )
    fig.update_layout(height=220, margin=dict(t=40, b=10, l=20, r=20))
    return fig


def jauge_risque(score: float, categorie: str) -> go.Figure:
    couleur = COULEUR_RISQUE.get(categorie, "#888")
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score * 100,
            title={
                "text": f"Score de risque — {categorie.upper()}",
                "font": {"size": 14},
            },
            number={"suffix": "%", "valueformat": ".1f"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": couleur},
                "steps": [
                    {"range": [0, 25], "color": "#d4edda"},
                    {"range": [25, 50], "color": "#fff3cd"},
                    {"range": [50, 75], "color": "#ffe0b2"},
                    {"range": [75, 100], "color": "#f8d7da"},
                ],
            },
        )
    )
    fig.update_layout(height=220, margin=dict(t=40, b=10, l=20, r=20))
    return fig


def jauge_prime(prime: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=prime,
            title={"text": "Prime annuelle (USD)", "font": {"size": 14}},
            number={"prefix": "$", "valueformat": ",.0f"},
            gauge={
                "axis": {"range": [0, 5000], "tickformat": "$,.0f"},
                "bar": {"color": "#59a14f"},
                "steps": [
                    {"range": [0, 500], "color": "#d4edda"},
                    {"range": [500, 1500], "color": "#fff3cd"},
                    {"range": [1500, 5000], "color": "#f8d7da"},
                ],
            },
        )
    )
    fig.update_layout(height=220, margin=dict(t=40, b=10, l=20, r=20))
    return fig


def graphique_repartition_risque(repartition: dict) -> go.Figure:
    categories = ["faible", "moyen", "eleve", "critique"]
    valeurs = [repartition.get(c, 0) for c in categories]
    couleurs = [COULEUR_RISQUE[c] for c in categories]

    fig = go.Figure(
        go.Bar(
            x=categories,
            y=valeurs,
            marker_color=couleurs,
            text=valeurs,
            textposition="auto",
        )
    )
    fig.update_layout(
        title="Répartition des risques (prédictions)",
        xaxis_title="Catégorie",
        yaxis_title="Nombre",
        height=300,
        margin=dict(t=50, b=30, l=30, r=20),
    )
    return fig


def graphique_metriques_ml(meta: dict) -> go.Figure:
    """Affiche un radar des métriques ML à partir du metadata.json."""
    reg = meta.get("regression", {}).get("metriques_test", {})
    clf = meta.get("classification", {}).get("metriques_test", {})

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Régression",
            x=["R²", "MAE (k$)", "RMSE (k$)"],
            y=[
                reg.get("r2", 0),
                reg.get("mae", 0) / 1000,
                reg.get("rmse", 0) / 1000,
            ],
            marker_color="#4e79a7",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Classification",
            x=["Accuracy", "F1 macro", "Précision"],
            y=[
                clf.get("accuracy", 0),
                clf.get("f1_macro", 0),
                clf.get("precision_macro", 0),
            ],
            marker_color="#59a14f",
        )
    )
    fig.update_layout(
        title="Métriques des modèles ML",
        barmode="group",
        height=320,
        margin=dict(t=50, b=30, l=30, r=20),
        yaxis=dict(range=[0, 1.1]),
    )
    return fig
