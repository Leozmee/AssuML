"""
Router prédictions ML — AssuML API.

Endpoints de scoring assurantiel basés sur les modèles ML entraînés.
Préfixe monté sur /api dans api/main.py.

Routes :
  POST /api/predict/cout     — coût médical prédit (régression)
  POST /api/predict/risque   — catégorie et score de risque (classification)
  POST /api/predict/complet  — orchestration complète + scoring business
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database.crud as crud
from api.dependencies import get_db
from api.schemas.prediction import (
    PredictCompletResponse,
    PredictCoutResponse,
    PredictRequest,
    PredictRisqueResponse,
)

router = APIRouter(prefix="/predict", tags=["ml"])


def _extraire_features(body: PredictRequest) -> dict:
    """Extrait les features du body Pydantic pour les fonctions predict_*.

    Returns:
        dict: Paramètres nommés attendus par predict_cost et predict_risk.
    """
    return {
        "age": body.age,
        "sexe": body.sexe,
        "imc": body.imc,
        "enfants": body.enfants,
        "fumeur": body.fumeur,
        "region": body.region,
    }


@router.post("/cout", response_model=PredictCoutResponse)
def predict_cout(body: PredictRequest, db: Session = Depends(get_db)):
    """Prédit le coût médical annuel en USD pour un profil assuré.

    Args:
        body: Vecteur de caractéristiques (PredictRequest).
        db: Session SQLAlchemy injectée (non utilisée ici, présente pour cohérence).

    Returns:
        PredictCoutResponse avec le coût prédit.

    Raises:
        HTTPException 500: Si le modèle .pkl est absent.
    """
    try:
        from ml_models.prediction.predict import predict_cost

        cout = predict_cost(**_extraire_features(body))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return PredictCoutResponse(cout_predit=cout)


@router.post("/risque", response_model=PredictRisqueResponse)
def predict_risque(body: PredictRequest, db: Session = Depends(get_db)):
    """Prédit la catégorie de risque et le score de confiance.

    Args:
        body: Vecteur de caractéristiques (PredictRequest).
        db: Session SQLAlchemy injectée.

    Returns:
        PredictRisqueResponse avec categorie_risque et score_risque.

    Raises:
        HTTPException 500: Si le modèle .pkl est absent.
    """
    try:
        from ml_models.prediction.predict import predict_risk

        categorie, score = predict_risk(**_extraire_features(body))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return PredictRisqueResponse(categorie_risque=categorie, score_risque=score)


@router.post("/complet", response_model=PredictCompletResponse)
def predict_complet(body: PredictRequest, db: Session = Depends(get_db)):
    """Orchestration complète : deux modèles + logique métier + persistance optionnelle.

    Pipeline :
      1. predict_cost()        → cout_predit
      2. predict_risk()        → (categorie_risque, score_risque)
      3. calculer_prime()      → prime
      4. get_decision()        → decision
      5. Si client_id fourni   → persiste dans predictions

    Args:
        body: Vecteur de caractéristiques avec client_id optionnel.
        db: Session SQLAlchemy injectée.

    Returns:
        PredictCompletResponse avec tous les résultats et prediction_id (ou None).

    Raises:
        HTTPException 400: Si client_id fourni mais client inexistant ou inactif.
        HTTPException 500: Si un modèle .pkl est absent.
    """
    try:
        from ml_models.prediction.predict import predict_cost, predict_risk

        features = _extraire_features(body)
        cout = predict_cost(**features)
        categorie, score = predict_risk(**features)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    from business.scoring import calculer_prime
    from business.risk_engine import get_decision

    prime = calculer_prime(cout, categorie)
    decision = get_decision(categorie)

    # Persistance optionnelle si client_id fourni
    prediction_id = None
    if body.client_id is not None:
        client = crud.get_client(db, body.client_id)
        if client is None or client.date_suppression is not None:
            raise HTTPException(
                status_code=400,
                detail=f"Client {body.client_id} introuvable ou inactif",
            )
        prediction = crud.create_prediction(
            db,
            client_id=body.client_id,
            cout_predit=cout,
            score_risque=score,
            categorie_risque=categorie,
            decision=decision,
            prime=prime,
            version_modele="v1",
        )
        prediction_id = prediction.prediction_id

    return PredictCompletResponse(
        cout_predit=cout,
        categorie_risque=categorie,
        score_risque=score,
        prime=prime,
        decision=decision,
        prediction_id=prediction_id,
    )
