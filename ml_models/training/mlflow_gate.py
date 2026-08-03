"""
Logique de comparaison et de promotion des modèles — MLflow.

Compare la métrique principale d'un nouveau run à celle du modèle actuellement
déployé (lue dans metadata.json) avant d'autoriser son déploiement, et gère la
promotion au Model Registry MLflow via un alias (pas de stages — dépréciés
depuis MLflow 2.9.0).

Utilisé par train_regression.py et train_classification.py.
"""

import json
import os

import mlflow
from mlflow.tracking import MlflowClient


def lire_metrique_actuelle(metadata_path, cle_modele, cle_metrique):
    """Lit la métrique principale du modèle actuellement déployé.

    Args:
        metadata_path (str): Chemin vers metadata.json.
        cle_modele (str): "regression" ou "classification".
        cle_metrique (str): Nom de la métrique (ex. "r2", "accuracy").

    Returns:
        float | None: La métrique actuelle, ou None si metadata.json est absent
        ou si la clé n'existe pas encore (premier entraînement).
    """
    if not os.path.exists(metadata_path):
        return None
    with open(metadata_path, encoding="utf-8") as f:
        meta = json.load(f)
    return meta.get(cle_modele, {}).get("metriques_test", {}).get(cle_metrique)


def est_meilleur_modele(nouvelle_metrique, metrique_actuelle):
    """Détermine si le nouveau modèle doit remplacer celui en production.

    Args:
        nouvelle_metrique (float): Métrique du nouveau run (ex. r2, accuracy).
        metrique_actuelle (float | None): Métrique du modèle actuellement
            déployé (None si aucune baseline n'existe encore).

    Returns:
        bool: True si nouvelle_metrique est strictement supérieure à
        metrique_actuelle, ou si aucune baseline n'existe encore.
    """
    if metrique_actuelle is None:
        return True
    return nouvelle_metrique > metrique_actuelle


def promouvoir_modele(nom_modele, model_id):
    """Enregistre le Logged Model dans le Registry et assigne l'alias "production".

    MLflow 3.x logue le modèle via l'entité "Logged Model" (mlflow.last_logged_model(),
    identifiée par model_id) plutôt que sous un chemin d'artefact fixe du run
    (l'ancienne convention "runs:/<run_id>/model" n'est plus fiable avec
    mlflow.sklearn.autolog() sur cette version).

    L'alias "production" est réassigné à cette nouvelle version. Contrairement à
    l'ancien mécanisme de stages (transition_model_version_stage, déprécié
    depuis MLflow 2.9.0), les alias n'ont pas de rétrogradation automatique :
    l'ancienne version reste consultable dans l'historique, simplement sans
    l'alias "production".

    Args:
        nom_modele (str): Nom du Registered Model (ex. "assuml-regression").
        model_id (str): Identifiant du Logged Model (mlflow.last_logged_model()).
    """
    model_uri = f"models:/{model_id}"
    version = mlflow.register_model(model_uri, nom_modele)

    client = MlflowClient()
    client.set_registered_model_alias(nom_modele, "production", version.version)
    print(f"✅ {nom_modele} v{version.version} — alias 'production' assigné")
