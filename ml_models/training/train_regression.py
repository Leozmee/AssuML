"""
Script d'entraînement standalone — Modèle de Régression.

Usage :
    python -m ml_models.training.train_regression            # entraînement
    python -m ml_models.training.train_regression --search    # GridSearchCV

Fichiers produits :
    ml_models/saved_models/regression.pkl  — Pipeline sklearn complet (gitignored)
    ml_models/saved_models/metadata.json   — Métriques + hyperparamètres (commité)


Données d'entrée :
    data/processed/features.csv — produit par notebooks/02_feature_engineering.ipynb

Constitution AssuML — Principes respectés :
    - Principe II  : preprocessing fit uniquement sur X_train, random_state=42
    - Principe IV  : .pkl non commité (.gitignore), pas de credentials
    - Principe V   : docstrings français, PEP8
"""

import json
import os
import sys
from datetime import date

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml_models.training.mlflow_gate import (
    est_meilleur_modele,
    lire_metrique_actuelle,
    promouvoir_modele,
)

# --- Constantes ---
DATA_PATH = os.path.join("data", "processed", "features.csv")
MODEL_DIR = os.path.join("ml_models", "saved_models")
MODEL_PATH = os.path.join(MODEL_DIR, "regression.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "metadata.json")

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
TARGET_COL = "charges"
NUMERIC_COLS = ["age", "imc", "enfants"]
PASSTHROUGH_COLS = [
    "sexe",
    "fumeur",
    "region_northwest",
    "region_southeast",
    "region_southwest",
]

# Hyperparamètres — historique de recherche
# ------------------------------------------
# Origine : grille GridSearchCV (cv=5, scoring='r2') — notebook 03, Section 5 —
#   n_estimators=[100,200], max_depth=[3,4,5], min_samples_split=[2,5],
#   min_samples_leaf=[1,2] → 24 combinaisons x 5 folds, résultat retenu :
#   (200, 4, 2, 1). Cette grille ne testait ni learning_rate ni subsample.
#
# Revu le 2026-07-01 : la config (200, 4, 2, 1) présentait un sur-apprentissage
# net (R² train=0.9554 vs test=0.8533, écart=0.102). Une grille élargie
# (rechercher_hyperparametres() ci-dessous, 432 combinaisons x 5 folds) incluant
# learning_rate et subsample a trouvé une config bien plus robuste :
#   (100, 2, 5, 1, learning_rate=0.1, subsample=0.8)
#   → R² test=0.8806 (vs 0.8533), écart train-test=-0.003 (quasi nul),
#   R² CV dataset complet=0.8600±0.0301 (vs 0.8315±0.0429), MAE test=2441.96$
#   (vs 2666.63$). Amélioration sur toutes les métriques, adoptée.
BEST_PARAMS = {
    "n_estimators": 100,
    "max_depth": 2,
    "min_samples_split": 5,
    "min_samples_leaf": 1,
    "learning_rate": 0.1,
    "subsample": 0.8,
}

RANDOM_STATE = 42


def charger_donnees():
    """Charge features.csv et retourne X et y.

    Returns:
        tuple: (X, y) — DataFrame features et Series target.

    Raises:
        FileNotFoundError: Si features.csv est absent.
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Dataset introuvable : {DATA_PATH}\n"
            "Exécuter d'abord : notebooks/02_feature_engineering.ipynb"
        )
    df = pd.read_csv(DATA_PATH)
    print(f"✅ Dataset chargé : {len(df)} lignes, {len(FEATURE_COLS)} features")
    return df[FEATURE_COLS], df[TARGET_COL]


def construire_pipeline():
    """Construit le Pipeline sklearn (ColumnTransformer + GradientBoostingRegressor).

    Le ColumnTransformer applique StandardScaler sur les variables numériques
    continues (age, imc, enfants) et passe les variables binaires/one-hot
    sans transformation.

    Returns:
        Pipeline: Pipeline sklearn prêt pour fit().
    """
    preprocesseur = ColumnTransformer(
        [
            ("scaler", StandardScaler(), NUMERIC_COLS),
            ("passthrough", "passthrough", PASSTHROUGH_COLS),
        ]
    )
    modele = GradientBoostingRegressor(
        random_state=RANDOM_STATE,
        **BEST_PARAMS,
    )
    return Pipeline(
        [
            ("preprocessor", preprocesseur),
            ("model", modele),
        ]
    )


def calculer_metriques(y_true, y_pred):
    """Calcule R², MAE et RMSE.

    Args:
        y_true: Valeurs réelles.
        y_pred: Valeurs prédites.

    Returns:
        dict: Dictionnaire avec clés 'r2', 'mae', 'rmse'.
    """
    return {
        "r2": round(float(r2_score(y_true, y_pred)), 4),
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 2),
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 2),
    }


def sauvegarder_pipeline(pipeline):
    """Sérialise le pipeline dans regression.pkl via joblib.

    Args:
        pipeline: Pipeline sklearn entraîné.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"✅ Pipeline sauvegardé : {MODEL_PATH}")


def sauvegarder_metadata(metriques_test, metriques_cv, best_params, version_mlflow):
    """Sauvegarde les métadonnées d'entraînement dans metadata.json.

    Champs sauvegardés : version, date, algorithme, hyperparamètres,
    métriques test, métriques cross-validation, features, target, split,
    random_state.

    Args:
        metriques_test (dict): R², MAE, RMSE sur le test set.
        metriques_cv (dict): Moyenne et écart-type R² sur 5 folds.
        best_params (dict): Hyperparamètres du modèle final.
        version_mlflow (str): Numéro de version attribué par le Registry
            MLflow (promouvoir_modele) — garde le lien entre ce fichier et
            l'entrée MLflow réellement promue "production".
    """
    metadata = {
        "version": version_mlflow,
        "date_entrainement": str(date.today()),
        "algorithme": "GradientBoostingRegressor",
        "hyperparametres": best_params,
        "metriques_test": metriques_test,
        "metriques_cv": metriques_cv,
        "features": FEATURE_COLS,
        "target": TARGET_COL,
        "split": "80/20",
        "random_state": RANDOM_STATE,
    }
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✅ Metadata sauvegardée : {METADATA_PATH}")


def rechercher_hyperparametres():
    """Relance le GridSearchCV de vérification des BEST_PARAMS (essai 2026-07-01).

    Reproduit le split de main() (train_test_split, test_size=0.2, random_state=42)
    et explore une grille élargie autour de la config d'origine du notebook 03,
    incluant learning_rate et subsample — jamais testés dans la grille d'origine
    (24 combinaisons, cf. commentaire au-dessus de BEST_PARAMS).

    N'est pas appelée par main() ; à lancer explicitement via
    `python -m ml_models.training.train_regression --search`.
    """
    X, y = charger_donnees()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    pipeline_gs = Pipeline(
        [
            (
                "preprocessor",
                ColumnTransformer(
                    [
                        ("scaler", StandardScaler(), NUMERIC_COLS),
                        ("passthrough", "passthrough", PASSTHROUGH_COLS),
                    ]
                ),
            ),
            ("model", GradientBoostingRegressor(random_state=RANDOM_STATE)),
        ]
    )

    param_grid = {
        "model__n_estimators": [100, 150, 200],
        "model__max_depth": [2, 3, 4, 5],
        "model__min_samples_split": [2, 5, 10],
        "model__min_samples_leaf": [1, 2],
        "model__learning_rate": [0.05, 0.1, 0.2],
        "model__subsample": [0.8, 1.0],
    }
    n_combos = 1
    for valeurs in param_grid.values():
        n_combos *= len(valeurs)
    print(f"Grille : {n_combos} combinaisons x 5 folds = {n_combos * 5} fits")

    grid_search = GridSearchCV(
        pipeline_gs, param_grid, cv=5, scoring="r2", n_jobs=-1, verbose=1
    )
    grid_search.fit(X_train, y_train)

    print(f"\n✅ Meilleurs hyperparamètres : {grid_search.best_params_}")
    print(f"   R² CV moyen (X_train) : {grid_search.best_score_:.4f}")

    y_pred_gs = grid_search.best_estimator_.predict(X_test)
    print("\n--- Métriques test (candidat GridSearchCV) ---")
    print(f"R²  : {r2_score(y_test, y_pred_gs):.4f}")
    print(f"MAE : {mean_absolute_error(y_test, y_pred_gs):.2f} $")

    baseline = construire_pipeline()
    baseline.fit(X_train, y_train)
    y_pred_baseline = baseline.predict(X_test)
    print("\n--- Métriques test (BEST_PARAMS actuels) ---")
    print(f"R²  : {r2_score(y_test, y_pred_baseline):.4f}")
    print(f"MAE : {mean_absolute_error(y_test, y_pred_baseline):.2f} $")


def main():
    """Point d'entrée principal du script d'entraînement."""
    print("=" * 55)
    print("  Entraînement — Modèle de Régression AssuML")
    print("=" * 55)

    load_dotenv()
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow.set_experiment("assuml-regression")

    with mlflow.start_run():
        mlflow.sklearn.autolog()

        # 1. Chargement des données
        X, y = charger_donnees()

        # 2. Split 80/20 — random_state fixe pour reproductibilité
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=RANDOM_STATE
        )
        print(f"   X_train={X_train.shape[0]} lignes | X_test={X_test.shape[0]} lignes")

        # 3. Construction et entraînement du pipeline
        print("\nEntraînement du pipeline (GradientBoostingRegressor)...")
        pipeline = construire_pipeline()
        pipeline.fit(X_train, y_train)

        # 4. Métriques sur le test set
        y_pred = pipeline.predict(X_test)
        metriques_test = calculer_metriques(y_test, y_pred)
        print("\n--- Métriques finales (test set 20%) ---")
        print(f"R²   : {metriques_test['r2']:.4f}")
        print(f"MAE  : {metriques_test['mae']:.2f} USD")
        print(f"RMSE : {metriques_test['rmse']:.2f} USD")

        # 5. Cross-validation 5 plis pour la traçabilité
        print("\nCross-validation 5 plis...")
        cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring="r2", n_jobs=-1)
        metriques_cv = {
            "r2_mean": round(float(cv_scores.mean()), 4),
            "r2_std": round(float(cv_scores.std()), 4),
        }
        r2_mean = metriques_cv["r2_mean"]
        r2_std = metriques_cv["r2_std"]
        print(f"R² moyen CV : {r2_mean:.4f} ± {r2_std:.4f}")

        # 6. Logging explicite MLflow (params + métriques, complète l'autolog)
        mlflow.log_params(BEST_PARAMS)
        for cle, valeur in {**metriques_test, **metriques_cv}.items():
            mlflow.log_metric(cle, valeur)

        # 7. Gate anti-régression : ne déployer que si strictement meilleur
        metrique_actuelle = lire_metrique_actuelle(
            METADATA_PATH, "regression", "r2", model_path=MODEL_PATH
        )
        if est_meilleur_modele(metriques_test["r2"], metrique_actuelle):
            print()
            sauvegarder_pipeline(pipeline)
            logged_model = mlflow.last_logged_model()
            version_mlflow = promouvoir_modele(
                "assuml-regression", logged_model.model_id
            )
            sauvegarder_metadata(
                metriques_test, metriques_cv, BEST_PARAMS, version_mlflow
            )
        else:
            print(
                f"\n⚠️  Modèle non déployé — R²={metriques_test['r2']:.4f} "
                f"≤ R² actuel={metrique_actuelle:.4f}. "
                "regression.pkl conservé, run tracké dans MLflow."
            )

    print("\n✅ Entraînement terminé avec succès.")
    print("=" * 55)


if __name__ == "__main__":
    if "--search" in sys.argv:
        rechercher_hyperparametres()
    else:
        main()
