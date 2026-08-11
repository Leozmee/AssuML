"""Tests unitaires pour ml_models/training/mlflow_gate.py."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml_models.training.mlflow_gate import (  # noqa: E402
    est_meilleur_modele,
    lire_metrique_actuelle,
)


# ── Tests est_meilleur_modele ───────────────────────────────────────────────


def test_nouvelle_metrique_superieure_deploie():
    """Nouvelle métrique strictement supérieure → déploiement autorisé."""
    assert est_meilleur_modele(0.90, 0.88) is True


def test_nouvelle_metrique_inferieure_ne_deploie_pas():
    """Nouvelle métrique strictement inférieure → déploiement refusé."""
    assert est_meilleur_modele(0.85, 0.88) is False


def test_nouvelle_metrique_egale_ne_deploie_pas():
    """Métrique égale à l'actuelle → pas de remplacement sans gain mesurable."""
    assert est_meilleur_modele(0.88, 0.88) is False


def test_aucune_baseline_deploie_toujours():
    """Aucun modèle actuel (premier entraînement) → déploiement autorisé."""
    assert est_meilleur_modele(0.50, None) is True


# ── Tests lire_metrique_actuelle ────────────────────────────────────────────


def test_lire_metrique_actuelle_fichier_absent(tmp_path):
    """metadata.json absent → retourne None."""
    chemin = os.path.join(tmp_path, "metadata_inexistant.json")
    assert lire_metrique_actuelle(chemin, "regression", "r2") is None


def test_lire_metrique_actuelle_cle_absente(tmp_path):
    """metadata.json présent mais sans la clé demandée → retourne None."""
    chemin = os.path.join(tmp_path, "metadata.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"classification": {"metriques_test": {"accuracy": 0.9}}}, f)
    assert lire_metrique_actuelle(chemin, "regression", "r2") is None


def test_lire_metrique_actuelle_valeur_presente(tmp_path):
    """metadata.json présent avec la clé demandée → retourne la valeur."""
    chemin = os.path.join(tmp_path, "metadata.json")
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"regression": {"metriques_test": {"r2": 0.8533}}}, f)
    assert lire_metrique_actuelle(chemin, "regression", "r2") == 0.8533


def test_lire_metrique_actuelle_pkl_absent_ignore_metadata(tmp_path):
    """metadata.json présent (ex. committé en CI) mais .pkl absent (gitignoré,
    jamais checkouté) → traité comme aucune baseline, pas comme un blocage.
    Reproduit le bug CI où metadata.json était committé sans le .pkl associé,
    empêchant tout premier entraînement en environnement neuf de se déployer.
    """
    metadata_path = os.path.join(tmp_path, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({"regression": {"metriques_test": {"r2": 0.8806}}}, f)
    pkl_inexistant = os.path.join(tmp_path, "regression.pkl")
    assert (
        lire_metrique_actuelle(
            metadata_path, "regression", "r2", model_path=pkl_inexistant
        )
        is None
    )


def test_lire_metrique_actuelle_pkl_present_lit_metadata(tmp_path):
    """metadata.json et .pkl tous deux présents → la métrique est bien lue
    (cas normal, modèle réellement déployé)."""
    metadata_path = os.path.join(tmp_path, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({"regression": {"metriques_test": {"r2": 0.8806}}}, f)
    pkl_path = os.path.join(tmp_path, "regression.pkl")
    with open(pkl_path, "wb") as f:
        f.write(b"contenu-pkl-factice")
    assert (
        lire_metrique_actuelle(metadata_path, "regression", "r2", model_path=pkl_path)
        == 0.8806
    )
