"""
Tests unitaires pour predict_cost() — ml_models/prediction/predict.py.

Constitution Principe V : toute fonctionnalité livrée doit être couverte
par au moins un test pytest.
"""

import pytest

from ml_models.prediction.predict import predict_cost


# --- Profil de référence pour les tests ---
PROFIL_BASE = dict(age=45, sexe=1, imc=32.0, enfants=2, fumeur=0, region="southeast")


def test_predict_cost_returns_float():
    """predict_cost() doit retourner un float positif dans une plage réaliste."""
    resultat = predict_cost(**PROFIL_BASE)
    assert isinstance(resultat, float), f"Attendu float, obtenu {type(resultat)}"
    assert (
        500 < resultat < 100_000
    ), f"Prédiction hors plage réaliste : {resultat:.2f} USD"


def test_predict_cost_smoker_higher():
    """Un fumeur doit avoir un coût prédit supérieur à un non-fumeur."""
    cout_non_fumeur = predict_cost(**{**PROFIL_BASE, "fumeur": 0})
    cout_fumeur = predict_cost(**{**PROFIL_BASE, "fumeur": 1})
    assert (
        cout_fumeur > cout_non_fumeur
    ), f"Fumeur ({cout_fumeur:.2f}) devrait être > non-fumeur ({cout_non_fumeur:.2f})"


def test_predict_cost_all_regions():
    """predict_cost() doit fonctionner sans erreur pour les 4 régions."""
    regions = ["northeast", "northwest", "southeast", "southwest"]
    for region in regions:
        resultat = predict_cost(**{**PROFIL_BASE, "region": region})
        assert isinstance(resultat, float), f"Erreur pour region='{region}'"
        assert resultat > 0, f"Prédiction négative pour region='{region}' : {resultat}"


def test_predict_cost_missing_pkl(tmp_path, monkeypatch):
    """predict_cost() doit lever FileNotFoundError si regression.pkl est absent."""
    import ml_models.prediction.predict as predict_module

    # Forcer le rechargement avec un chemin inexistant
    chemin_original = predict_module.MODEL_PATH
    monkeypatch.setattr(predict_module, "MODEL_PATH", str(tmp_path / "inexistant.pkl"))
    monkeypatch.setattr(predict_module, "_pipeline", None)

    with pytest.raises((FileNotFoundError, OSError)):
        predict_cost(**PROFIL_BASE)

    # Restaurer pour ne pas affecter les autres tests
    monkeypatch.setattr(predict_module, "MODEL_PATH", chemin_original)
    monkeypatch.setattr(predict_module, "_pipeline", None)
