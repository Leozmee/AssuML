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


def registre_actif() -> bool:
    """Indique si le Model Registry MLflow doit être sollicité.

    Le registre vit dans un SQLite local (mlflow.db, gitignoré). Sur un
    environnement reconstruit à chaque déploiement, ce fichier repart vide :
    register_model() y attribuerait alors la version 1 à un modèle qui porte
    déjà un numéro bien plus élevé dans le registre de référence, et
    metadata.json — committé, donc source de vérité — serait écrasé par ce 1.

    Poser MLFLOW_ENABLED=false sur un tel environnement laisse le tracking
    fonctionner mais neutralise la promotion au Registry : le numéro de
    version déjà inscrit dans metadata.json est conservé tel quel.

    Returns:
        bool: False si MLFLOW_ENABLED vaut false/0/no (insensible à la
        casse), True par défaut.
    """
    return os.getenv("MLFLOW_ENABLED", "true").strip().lower() not in (
        "false",
        "0",
        "no",
    )


def version_publiee(metadata_path, cle_modele):
    """Relit le numéro de version déjà inscrit dans metadata.json.

    Utilisé lorsque le Registry est neutralisé (cf. registre_actif) : le
    numéro conservé est celui de l'exécution de référence, versionnée dans
    Git, et non celui qu'un registre éphémère viendrait d'inventer.

    Gère l'ancien format plat (régression à la racine) autant que le format
    imbriqué actuel.

    Args:
        metadata_path (str): Chemin vers metadata.json.
        cle_modele (str): "regression" ou "classification".

    Returns:
        str | None: Le numéro de version, ou None si le fichier est absent,
        illisible, ou ne contient pas encore ce modèle.
    """
    try:
        with open(metadata_path, encoding="utf-8") as f:
            meta = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    bloc = meta.get(cle_modele)
    if bloc is None and cle_modele == "regression" and "algorithme" in meta:
        bloc = meta  # ancien format plat, régression uniquement
    if not isinstance(bloc, dict):
        return None
    return bloc.get("version")


def lire_metrique_actuelle(metadata_path, cle_modele, cle_metrique, model_path=None):
    """Lit la métrique principale du modèle actuellement déployé.

    metadata.json est committé dans le dépôt (source de vérité constitutionnelle)
    alors que les .pkl sont gitignorés — sur un checkout neuf (ex. CI), metadata.json
    peut donc exister sans qu'aucun .pkl ne soit réellement présent sur disque.
    Sans model_path, la fonction croirait alors qu'un modèle est déjà déployé et
    bloquerait le tout premier entraînement du run. Si model_path est fourni et que
    ce fichier n'existe pas, on traite la situation comme "aucune baseline" — même
    comportement que l'absence de metadata.json.

    Args:
        metadata_path (str): Chemin vers metadata.json.
        cle_modele (str): "regression" ou "classification".
        cle_metrique (str): Nom de la métrique (ex. "r2", "accuracy").
        model_path (str | None): Chemin vers le .pkl déployé. Si fourni et absent,
            la métrique de metadata.json est ignorée (pas de modèle réellement
            déployé, quoi qu'en dise metadata.json).

    Returns:
        float | None: La métrique actuelle, ou None si metadata.json ou le .pkl
        associé sont absents, ou si la clé n'existe pas encore (premier
        entraînement).
    """
    if not os.path.exists(metadata_path):
        return None
    if model_path is not None and not os.path.exists(model_path):
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

    Returns:
        str: Le numéro de version attribué par le Registry (ex. "3"), à
        reporter dans metadata.json pour garder le lien entre le modèle
        servi et son entrée MLflow — sans quoi metadata.json ne permet pas
        de savoir quelle version du Registry est réellement déployée.
    """
    model_uri = f"models:/{model_id}"
    version = mlflow.register_model(model_uri, nom_modele)

    client = MlflowClient()
    client.set_registered_model_alias(nom_modele, "production", version.version)
    print(f"✅ {nom_modele} v{version.version} — alias 'production' assigné")
    return version.version
