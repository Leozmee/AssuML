"""
Moteur de règles métier pour l'évaluation du risque assuré.

Détermine la catégorie de risque à partir du coût prédit et
la décision de souscription à partir de la catégorie de risque.
"""

# Seuils de coût définissant les catégories de risque (USD)
SEUILS = [
    (5_000, "faible"),
    (15_000, "moyen"),
    (30_000, "eleve"),
]

# Décisions de souscription par catégorie de risque
DECISIONS = {
    "faible": "accepter",
    "moyen": "accepter",
    "eleve": "examiner",
    "critique": "refuser",
}


def get_categorie_risque(cout_predit: float) -> str:
    """Détermine la catégorie de risque à partir du coût médical prédit.

    Seuils :
      - < 5 000 USD    → faible
      - 5 000–14 999   → moyen
      - 15 000–29 999  → eleve
      - ≥ 30 000 USD   → critique

    Args:
        cout_predit: Coût médical annuel prédit par le modèle de régression (USD).

    Returns:
        Catégorie de risque : 'faible', 'moyen', 'eleve' ou 'critique'.
    """
    for seuil, categorie in SEUILS:
        if cout_predit < seuil:
            return categorie
    return "critique"


def get_decision(categorie_risque: str) -> str:
    """Retourne la décision de souscription pour une catégorie de risque donnée.

    Mapping :
      - faible / moyen → accepter
      - eleve          → examiner
      - critique       → refuser

    Args:
        categorie_risque: Catégorie — 'faible', 'moyen', 'eleve' ou 'critique'.

    Returns:
        Décision de souscription : 'accepter', 'examiner' ou 'refuser'.

    Raises:
        ValueError: Si la catégorie de risque n'est pas reconnue.
    """
    if categorie_risque not in DECISIONS:
        raise ValueError(
            f"Catégorie de risque inconnue : '{categorie_risque}'. "
            f"Valeurs acceptées : {list(DECISIONS.keys())}"
        )
    return DECISIONS[categorie_risque]
