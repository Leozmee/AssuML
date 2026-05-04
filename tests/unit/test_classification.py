"""Tests unitaires pour predict_risk() — ml_models/prediction/predict.py."""

import os
import sys

import pytest

# Ajout de la racine du projet au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_predict_risk_returns_tuple():
    """predict_risk() doit retourner un tuple (str, float)."""
    from ml_models.prediction.predict import predict_risk

    result = predict_risk(
        age=35, sexe=0, imc=25.0, enfants=1, fumeur=0, region="northeast"
    )
    assert isinstance(result, tuple), "Le résultat doit être un tuple"
    assert len(result) == 2, "Le tuple doit contenir exactement 2 éléments"
    categorie, score = result
    assert isinstance(categorie, str), "La catégorie doit être une chaîne"
    assert isinstance(score, float), "Le score doit être un float"
    assert categorie in {
        "faible",
        "moyen",
        "eleve",
        "critique",
    }, f"Catégorie inconnue : {categorie}"
    assert 0.0 <= score <= 1.0, f"Score hors [0,1] : {score}"


def test_predict_risk_smoker_eleve_or_critique():
    """Un profil fumeur avec IMC élevé doit être classifié 'eleve' ou 'critique'."""
    from ml_models.prediction.predict import predict_risk

    categorie, score = predict_risk(
        age=45, sexe=1, imc=32.0, enfants=2, fumeur=1, region="southeast"
    )
    assert categorie in {
        "eleve",
        "critique",
    }, f"Profil fumeur IMC=32 attendu 'eleve' ou 'critique', obtenu : {categorie}"
    assert (
        score > 0.5
    ), f"Score de confiance trop faible pour un profil à risque : {score}"


def test_predict_risk_all_regions():
    """predict_risk() doit fonctionner pour les 4 régions sans erreur."""
    from ml_models.prediction.predict import predict_risk

    regions = ["northeast", "northwest", "southeast", "southwest"]
    for region in regions:
        result = predict_risk(
            age=30, sexe=0, imc=22.0, enfants=0, fumeur=0, region=region
        )
        assert isinstance(result, tuple), f"Erreur pour la région : {region}"
        categorie, score = result
        assert categorie in {"faible", "moyen", "eleve", "critique"}


def test_predict_risk_missing_pkl(tmp_path, monkeypatch):
    """predict_risk() doit lever FileNotFoundError si classification.pkl est absent."""
    import ml_models.prediction.predict as pred_module

    # Réinitialisation du singleton pour ce test
    original_clf = pred_module._clf_pipeline
    pred_module._clf_pipeline = None

    fake_path = str(tmp_path / "absent.pkl")
    monkeypatch.setattr(pred_module, "CLF_PATH", fake_path)

    with pytest.raises(FileNotFoundError):
        pred_module._load_clf_pipeline()

    # Restauration
    pred_module._clf_pipeline = original_clf
