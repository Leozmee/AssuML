"""Tests de la barrière de non-régression CI (verifier_non_regression).

Le module compare les métriques fraîchement entraînées à celles du
metadata.json commité. Ces tests portent sur la logique de comparaison, pas
sur l'accès Git, qui est isolé dans lire_reference_committee().
"""

from ml_models.training.verifier_non_regression import comparer, lire_metriques

TOLERANCE = 0.001


def _meta(r2, f1):
    """Construit un metadata.json minimal au format imbriqué."""
    return {
        "regression": {"metriques_test": {"r2": r2}},
        "classification": {"metriques_test": {"f1_macro": f1}},
    }


def test_metriques_identiques_aucune_regression():
    """Une recette inchangée reproduit les mêmes métriques : rien à signaler."""
    ref = _meta(0.8806, 0.8685)
    assert comparer(ref, _meta(0.8806, 0.8685), TOLERANCE) == []


def test_amelioration_acceptee():
    """Un modèle meilleur que la référence passe sans objection."""
    ref = _meta(0.8806, 0.8685)
    assert comparer(ref, _meta(0.9100, 0.8900), TOLERANCE) == []


def test_regression_regression_detectee():
    """Une baisse du R² au-delà de la tolérance est signalée."""
    ref = _meta(0.8806, 0.8685)
    messages = comparer(ref, _meta(0.8600, 0.8685), TOLERANCE)
    assert len(messages) == 1
    assert "regression" in messages[0]


def test_regression_classification_detectee():
    """Une baisse du f1_macro est signalée au même titre."""
    ref = _meta(0.8806, 0.8685)
    messages = comparer(ref, _meta(0.8806, 0.8000), TOLERANCE)
    assert len(messages) == 1
    assert "classification" in messages[0]


def test_les_deux_modeles_peuvent_regresser():
    """Les deux régressions sont rapportées, pas seulement la première."""
    ref = _meta(0.8806, 0.8685)
    assert len(comparer(ref, _meta(0.8000, 0.8000), TOLERANCE)) == 2


def test_ecart_sous_la_tolerance_accepte():
    """Un écart de dernière décimale entre plateformes ne fait pas échouer."""
    ref = _meta(0.8806, 0.8685)
    assert comparer(ref, _meta(0.8801, 0.8680), TOLERANCE) == []


def test_metrique_absente_ignoree():
    """Un modèle absent de la référence n'est pas comparé, et ne bloque pas."""
    ref = {"regression": {"metriques_test": {"r2": 0.8806}}}
    assert comparer(ref, _meta(0.8806, 0.8685), TOLERANCE) == []


def test_lire_metriques_ancien_format_plat():
    """Le format plat historique (régression à la racine) reste lisible."""
    plat = {"algorithme": "GradientBoostingRegressor", "metriques_test": {"r2": 0.85}}
    assert lire_metriques(plat, "regression") == {"r2": 0.85}


def test_lire_metriques_bloc_absent():
    """Un bloc manquant retourne un dict vide plutôt que de lever."""
    assert lire_metriques({}, "classification") == {}
