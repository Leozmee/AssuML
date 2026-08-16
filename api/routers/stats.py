"""
Router statistiques KPIs — AssuML API.

Tableau de bord agrégé du portefeuille assurantiel, calculé en temps réel.
Préfixe monté sur /api dans api/main.py.

Routes :
  GET /api/stats/kpis — métriques agrégées du portefeuille
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.routers.ml import _decoder_version
from database.models import Client, Contrat, Prediction

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/kpis")
def obtenir_kpis(db: Session = Depends(get_db)) -> dict:
    """Retourne les KPIs agrégés du portefeuille en temps réel.

    Métriques calculées :
      - nb_clients_actifs    : clients sans date_suppression
      - nb_contrats_actifs   : contrats avec statut 'actif'
      - repartition_risque   : count par categorie_risque depuis predictions
      - cout_moyen_predit    : moyenne des cout_predit (None si aucune prédiction)

    Args:
        db: Session SQLAlchemy injectée.

    Returns:
        dict: 4 métriques agrégées.
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

    nb_predictions = sum(repartition_base.values())

    return {
        "nb_clients_actifs": nb_clients,
        "nb_contrats_actifs": nb_contrats,
        "nb_predictions": nb_predictions,
        "repartition_risque": repartition_base,
        "cout_moyen_predit": cout_moyen_arrondi,
    }


@router.get("/dernieres-predictions", response_model=List[dict])
def dernieres_predictions_par_client(db: Session = Depends(get_db)):
    """Retourne la dernière catégorie de risque prédite pour chaque client.

    Utilise une sous-requête pour récupérer la prédiction la plus récente
    (prediction_id max) par client_id.

    Returns:
        Liste de {client_id, categorie_risque} — un seul enregistrement par client.
    """
    latest = (
        db.query(
            Prediction.client_id,
            func.max(Prediction.prediction_id).label("latest_id"),
        )
        .group_by(Prediction.client_id)
        .subquery()
    )
    rows = (
        db.query(
            Prediction.client_id,
            Prediction.categorie_risque,
            Prediction.prime,
            Prediction.version_modele,
        )
        .join(latest, Prediction.prediction_id == latest.c.latest_id)
        .all()
    )
    return [
        {
            "client_id": r.client_id,
            "categorie_risque": r.categorie_risque,
            "prime": float(r.prime) if r.prime is not None else None,
            "inputs": _decoder_version(r.version_modele),
        }
        for r in rows
    ]
