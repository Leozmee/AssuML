"""
Module de nettoyage des données : renommage des colonnes Kaggle vers le nommage
métier français défini dans la constitution AssuML.
"""

import pandas as pd


# Mapping des noms de colonnes Kaggle → nommage français (constitution §2)
MAPPING_COLONNES = {
    "sex": "sexe",
    "bmi": "imc",
    "children": "enfants",
    "smoker": "fumeur",
}


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renomme les colonnes du dataset Kaggle vers le nommage métier français.

    Applique le mapping défini dans la constitution AssuML §2 :
    sex → sexe, bmi → imc, children → enfants, smoker → fumeur.
    Les colonnes non présentes dans le mapping (age, region, charges)
    sont conservées telles quelles.

    Paramètres :
        df : DataFrame avec les colonnes originales Kaggle.

    Retour :
        DataFrame avec les colonnes renommées. Le DataFrame original
        n'est pas modifié (opération non destructive).

    Exemple :
        >>> df = pd.read_csv('insurance.csv')
        >>> df_fr = rename_columns(df)
        >>> 'sexe' in df_fr.columns  # True
        >>> 'sex' in df_fr.columns   # False
    """
    return df.rename(columns=MAPPING_COLONNES)
