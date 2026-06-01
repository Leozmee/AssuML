"""
Module de calcul des primes d'assurance.

Applique un coefficient de risque au coût prédit par le modèle ML
pour obtenir la prime finale proposée à l'assuré.
"""

COEFFICIENTS = {
    "faible": 1.0,
    "moyen": 1.15,
    "eleve": 1.35,
    "critique": 1.60,
}


def calculer_prime(cout_predit: float, categorie_risque: str) -> float:
    """Calcule la prime d'assurance à partir du coût prédit et de la catégorie.

    Args:
        cout_predit: Coût médical annuel prédit par le modèle de régression (USD).
        categorie_risque: Catégorie — 'faible', 'moyen', 'eleve' ou 'critique'.

    Returns:
        Prime d'assurance finale (USD) = cout_predit × coefficient de la catégorie.

    Raises:
        KeyError: Si la catégorie de risque n'est pas reconnue.
    """
    return round(cout_predit * COEFFICIENTS[categorie_risque], 2)
