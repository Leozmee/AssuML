"""
Module de normalisation : encodage des variables catégorielles pour le machine
learning. Compatible avec les noms de colonnes français (après cleaning.py)
et les noms originaux Kaggle (compatibilité ascendante).
"""

import pandas as pd


# Mappings d'encodage (labels originaux et français acceptés)
_MAPPING_SEXE = {"female": 1, "male": 0, "femme": 1, "homme": 0}
_MAPPING_FUMEUR = {"yes": 1, "no": 0, "oui": 1, "non": 0}

# Catégorie de référence one-hot supprimée (constitution research.md feature 001)
_REGION_REFERENCE = "northeast"


def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Encode les variables catégorielles pour le machine learning.

    Applique les encodages suivants :
    - sexe (ou sex) : 'female'/'femme' → 1, 'male'/'homme' → 0
    - fumeur (ou smoker) : 'yes'/'oui' → 1, 'no'/'non' → 0
    - region : one-hot encoding avec drop_first=True
      (northeast supprimé comme référence, conforme à la constitution)

    Paramètres :
        df : DataFrame avec nommage français (sexe, fumeur) ou Kaggle
             (sex, smoker). La colonne region doit être présente.

    Retour :
        DataFrame avec les variables catégorielles encodées numériquement.
        Les colonnes originales sexe/sex et fumeur/smoker sont remplacées.
        La colonne region est remplacée par region_northwest, region_southeast,
        region_southwest (northeast = référence supprimée).

    Note :
        Cette fonction est une fonction pure — elle ne modifie pas le DataFrame
        original et ne lit/écrit aucun fichier.

    Exemple :
        >>> df_enc = encode_categoricals(df_fr)
        >>> df_enc['sexe'].isin([0, 1]).all()  # True
        >>> 'region_northeast' in df_enc.columns  # False (supprimé)
    """
    df = df.copy()

    # --- Encodage sexe ---
    if "sexe" in df.columns:
        df["sexe"] = df["sexe"].map(_MAPPING_SEXE).astype(int)
    elif "sex" in df.columns:
        df["sex"] = df["sex"].map(_MAPPING_SEXE).astype(int)

    # --- Encodage fumeur ---
    if "fumeur" in df.columns:
        df["fumeur"] = df["fumeur"].map(_MAPPING_FUMEUR).astype(int)
    elif "smoker" in df.columns:
        df["smoker"] = df["smoker"].map(_MAPPING_FUMEUR).astype(int)

    # --- One-hot encoding région (drop_first=True, northeast supprimé) ---
    if "region" in df.columns:
        df = pd.get_dummies(df, columns=["region"], drop_first=True)
        # Convertir les colonnes booléennes en int
        region_cols = [c for c in df.columns if c.startswith("region_")]
        for col in region_cols:
            df[col] = df[col].astype(int)

    return df
