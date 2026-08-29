"""POC — Comparaison de deux plateformes MLOps : MLflow et Weights & Biases.

Un seul entraînement, journalisé dans les deux backends, afin que les métriques
enregistrées de part et d'autre servent de témoin : elles doivent être identiques.
Ce qui est réellement comparé, ce sont les deux outils.

Ce script ne modifie RIEN du projet :
  - il ne sauvegarde aucun .pkl et ne touche pas à metadata.json ;
  - il écrit dans une expérience MLflow dédiée (poc-comparaison-mlops) ;
  - il produit deux exports JSON lus ensuite par la page Streamlit,
    pour que la démonstration ne dépende d'aucun réseau.

Usage :
    python -m poc.train_double                 # les deux backends
    python -m poc.train_double --sans-wandb    # MLflow seul
    python -m poc.train_double --hors-ligne    # W&B en mode offline (test réseau)
"""

import argparse
import importlib.util
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split

from ml_models.training.train_regression import (
    BEST_PARAMS,
    RANDOM_STATE,
    calculer_metriques,
    charger_donnees,
    construire_pipeline,
)

DOSSIER = Path(__file__).resolve().parent
EXPORT_MLFLOW = DOSSIER / "export_mlflow.json"
EXPORT_WANDB = DOSSIER / "export_wandb.json"

EXPERIENCE = "poc-comparaison-mlops"
PROJET_WANDB = "assuml-poc"

# Nombre d'appels propres à chaque SDK dans ce script — compté à la main et
# vérifiable par lecture. C'est le critère « coût d'intégration ».
LIGNES_INTEGRATION = {"mlflow": 7, "wandb": 5}


def poids_paquet(nom: str):
    """Retourne (taille en Mo, nombre de dépendances directes) d'un paquet installé."""
    spec = importlib.util.find_spec(nom)
    if spec is None or not spec.origin:
        return None, None
    racine = Path(spec.origin).parent
    octets = sum(f.stat().st_size for f in racine.rglob("*") if f.is_file())
    try:
        from importlib.metadata import requires

        deps = len(requires(nom) or [])
    except Exception:
        deps = None
    return round(octets / 1_000_000, 1), deps


def entrainer():
    """Exécute l'entraînement de référence et retourne pipeline, métriques, durée."""
    X, y = charger_donnees()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
    pipeline = construire_pipeline()
    debut = time.perf_counter()
    pipeline.fit(X_train, y_train)
    duree = time.perf_counter() - debut
    metriques = calculer_metriques(y_test, pipeline.predict(X_test))
    return pipeline, metriques, duree, len(X_train), len(X_test)


def journaliser_mlflow(metriques, duree_fit):
    """Journalise le run dans MLflow et mesure le surcoût de journalisation."""
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow.set_experiment(EXPERIENCE)

    debut = time.perf_counter()
    with mlflow.start_run(run_name="poc-mlflow") as run:
        mlflow.log_params(BEST_PARAMS)
        for cle, valeur in metriques.items():
            mlflow.log_metric(cle, valeur)
        run_id = run.info.run_id
    surcout = time.perf_counter() - debut

    taille, deps = poids_paquet("mlflow")
    return {
        "outil": "MLflow",
        "version": mlflow.__version__,
        "run_id": run_id,
        "experience": EXPERIENCE,
        "parametres": BEST_PARAMS,
        "metriques": metriques,
        "duree_fit_s": round(duree_fit, 3),
        "surcout_journalisation_s": round(surcout, 3),
        "lignes_integration": LIGNES_INTEGRATION["mlflow"],
        "compte_requis": False,
        "hors_ligne": "complet — magasin SQLite local, interface servie en local",
        "donnees_residentes": os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"),
        "sortie_du_perimetre_local": False,
        "taille_installee_mo": taille,
        "dependances_directes": deps,
        "exporte_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def journaliser_wandb(metriques, duree_fit, hors_ligne=False):
    """Journalise le même run dans W&B. Retourne None si le SDK est absent."""
    try:
        import wandb
    except ImportError:
        return None

    if hors_ligne:
        os.environ["WANDB_MODE"] = "offline"

    debut = time.perf_counter()
    run = wandb.init(
        project=PROJET_WANDB,
        name="poc-wandb",
        config=BEST_PARAMS,
        reinit=True,
    )
    wandb.log(metriques)
    identifiant = run.id
    url = run.url if not hors_ligne else None
    wandb.finish()
    surcout = time.perf_counter() - debut

    taille, deps = poids_paquet("wandb")
    return {
        "outil": "Weights & Biases",
        "version": wandb.__version__,
        "run_id": identifiant,
        "experience": PROJET_WANDB,
        "url": url,
        "parametres": BEST_PARAMS,
        "metriques": metriques,
        "duree_fit_s": round(duree_fit, 3),
        "surcout_journalisation_s": round(surcout, 3),
        "lignes_integration": LIGNES_INTEGRATION["wandb"],
        "compte_requis": True,
        "hors_ligne": (
            "partiel — l'entraînement aboutit, mais les runs ne sont "
            "consultables qu'après wandb sync"
            if hors_ligne
            else "non testé — exécution en ligne"
        ),
        "donnees_residentes": "serveurs W&B (cache local dans wandb/)",
        "sortie_du_perimetre_local": not hors_ligne,
        "taille_installee_mo": taille,
        "dependances_directes": deps,
        "mode": "offline" if hors_ligne else "online",
        "exporte_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sans-wandb", action="store_true", help="MLflow seul.")
    parser.add_argument(
        "--hors-ligne", action="store_true", help="Force W&B en mode offline."
    )
    options = parser.parse_args()

    print("=" * 60)
    print("  POC — MLflow vs Weights & Biases")
    print("=" * 60)

    pipeline, metriques, duree_fit, n_train, n_test = entrainer()
    print(f"\nEntraînement : {n_train} lignes / test {n_test} lignes")
    print(f"R² = {metriques['r2']:.4f} | MAE = {metriques['mae']:.2f} $")
    print(f"Durée du fit : {duree_fit:.3f} s")

    export_mlflow = journaliser_mlflow(metriques, duree_fit)
    EXPORT_MLFLOW.write_text(
        json.dumps(export_mlflow, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n✅ MLflow  → {EXPORT_MLFLOW.name}")

    if options.sans_wandb:
        print("⏭️  W&B ignoré (--sans-wandb)")
        return

    export_wandb = journaliser_wandb(metriques, duree_fit, options.hors_ligne)
    if export_wandb is None:
        print("⚠️  wandb absent — pip install -r poc/requirements-poc.txt")
        return
    EXPORT_WANDB.write_text(
        json.dumps(export_wandb, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"✅ W&B     → {EXPORT_WANDB.name}")
    print("\nOuvrez la page « Test Plateformes MLOps » dans Streamlit.")


if __name__ == "__main__":
    main()
