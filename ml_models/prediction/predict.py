"""
Fonction de prédiction du coût médical — interface production.

Expose predict_cost() pour être consommée par l'API FastAPI (feature 001).
Le pipeline est chargé une seule fois au niveau module (singleton).

Usage :
    from ml_models.prediction.predict import predict_cost
    cout = predict_cost(
        age=45, sexe=1, imc=32.0, enfants=2, fumeur=1, region='southeast'
    )
"""

import os

import joblib
import pandas as pd

# Chemin vers le pipeline sérialisé (relatif à la racine du projet)
MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "saved_models", "regression.pkl"
)

# Mapping région string → colonnes one-hot
# northeast est la catégorie de référence (drop_first=True) → tout à 0
REGION_MAPPING = {
    "northeast": {"region_northwest": 0, "region_southeast": 0, "region_southwest": 0},
    "northwest": {"region_northwest": 1, "region_southeast": 0, "region_southwest": 0},
    "southeast": {"region_northwest": 0, "region_southeast": 1, "region_southwest": 0},
    "southwest": {"region_northwest": 0, "region_southeast": 0, "region_southwest": 1},
}

# Ordre des colonnes attendu par le pipeline
# (doit correspondre à FEATURE_COLS dans train_regression.py)
FEATURE_COLS = [
    "age",
    "imc",
    "enfants",
    "sexe",
    "fumeur",
    "region_northwest",
    "region_southeast",
    "region_southwest",
]

# Singleton — chargé une seule fois à l'import du module
_pipeline = None


def _load_pipeline():
    """Charge regression.pkl si non encore chargé (singleton).

    Returns:
        Pipeline sklearn chargé depuis regression.pkl.

    Raises:
        FileNotFoundError: Si regression.pkl est absent du chemin attendu.
    """
    global _pipeline
    if _pipeline is None:
        chemin_abs = os.path.abspath(MODEL_PATH)
        if not os.path.exists(chemin_abs):
            raise FileNotFoundError(
                f"Modèle introuvable : {chemin_abs}\n"
                "Exécuter d'abord : python -m ml_models.training.train_regression"
            )
        _pipeline = joblib.load(chemin_abs)
    return _pipeline


def predict_cost(
    age: int,
    sexe: int,
    imc: float,
    enfants: int,
    fumeur: int,
    region: str,
) -> float:
    """Prédit le coût médical annuel en USD pour un profil assuré.

    Le pipeline embarque le preprocessing (StandardScaler sur les numériques,
    passthrough sur les binaires/one-hot) et le modèle GradientBoostingRegressor.
    La conversion region string → one-hot est effectuée en interne.

    Args:
        age (int): Âge de l'assuré (typiquement 18–64).
        sexe (int): Sexe encodé — 0 = homme, 1 = femme.
        imc (float): Indice de masse corporelle (typiquement 15–55).
        enfants (int): Nombre d'enfants à charge (0–5).
        fumeur (int): Statut fumeur — 0 = non-fumeur, 1 = fumeur.
        region (str): Région géographique — 'northeast', 'northwest',
                      'southeast' ou 'southwest'.

    Returns:
        float: Coût médical annuel prédit en USD.

    Raises:
        FileNotFoundError: Si regression.pkl est absent.
        KeyError: Si la valeur de `region` n'est pas dans REGION_MAPPING.
    """
    # Conversion region string → colonnes one-hot
    one_hot = REGION_MAPPING[region]

    # Construction du DataFrame 1-ligne dans l'ordre attendu par le pipeline
    donnees = {
        "age": age,
        "imc": imc,
        "enfants": enfants,
        "sexe": sexe,
        "fumeur": fumeur,
        "region_northwest": one_hot["region_northwest"],
        "region_southeast": one_hot["region_southeast"],
        "region_southwest": one_hot["region_southwest"],
    }
    df = pd.DataFrame([donnees])[FEATURE_COLS]

    prediction = _load_pipeline().predict(df)
    return float(prediction[0])
