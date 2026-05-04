"""
Router statistiques KPIs — AssuML API.

Tableau de bord agrégé du portefeuille assurantiel, calculé en temps réel.
Préfixe monté sur /api dans api/main.py.

Routes :
  GET /api/stats/kpis — métriques agrégées du portefeuille
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.dependencies import get_db
from database.models import Client, Contrat, Prediction, Sinistre

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/kpis")
def obtenir_kpis(db: Session = Depends(get_db)) -> dict:
    """Retourne les KPIs agrégés du portefeuille en temps réel.

    Métriques calculées :
      - nb_clients_actifs    : clients sans date_suppression
      - nb_contrats_actifs   : contrats avec statut 'actif'
      - sinistres_en_cours   : sinistres avec statut_sinistre 'en_cours'
      - repartition_risque   : count par categorie_risque depuis predictions
      - cout_moyen_predit    : moyenne des cout_predit (None si aucune prédiction)

    Args:
        db: Session SQLAlchemy injectée.

    Returns:
        dict: 5 métriques agrégées.
    """
    # Clients actifs
    nb_clients = (
        db.query(func.count(Client.client_id))
        .filter(Client.date_suppression.is_(None))
        .scalar()
        or 0
    )

    # Contrats actifs
    nb_contrats = (
        db.query(func.count(Contrat.contrat_id))
        .filter(Contrat.statut == "actif")
        .scalar()
        or 0
    )

    # Sinistres en cours
    nb_sinistres = (
        db.query(func.count(Sinistre.sinistre_id))
        .filter(Sinistre.statut_sinistre == "en_cours")
        .scalar()
        or 0
    )

    # Répartition par catégorie de risque
    repartition_base = {"faible": 0, "moyen": 0, "eleve": 0, "critique": 0}
    rows = (
        db.query(Prediction.categorie_risque, func.count(Prediction.prediction_id))
        .group_by(Prediction.categorie_risque)
        .all()
    )
    for categorie, count in rows:
        if categorie in repartition_base:
            repartition_base[categorie] = count

    # Coût moyen prédit
    cout_moyen = db.query(func.avg(Prediction.cout_predit)).scalar()
    cout_moyen_arrondi = round(float(cout_moyen), 2) if cout_moyen is not None else None

    return {
        "nb_clients_actifs": nb_clients,
        "nb_contrats_actifs": nb_contrats,
        "sinistres_en_cours": nb_sinistres,
        "repartition_risque": repartition_base,
        "cout_moyen_predit": cout_moyen_arrondi,
    }
