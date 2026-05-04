"""
Script d'entraînement standalone — Modèle de Régression.

Usage :
    python -m ml_models.training.train_regression

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
from datetime import date

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

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

# Hyperparamètres optimaux (issus de GridSearchCV — notebook 03)
BEST_PARAMS = {
    "n_estimators": 200,
    "max_depth": 4,
    "min_samples_split": 2,
    "min_samples_leaf": 1,
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


def sauvegarder_metadata(metriques_test, metriques_cv, best_params):
    """Sauvegarde les métadonnées d'entraînement dans metadata.json.

    Champs sauvegardés : version, date, algorithme, hyperparamètres,
    métriques test, métriques cross-validation, features, target, split,
    random_state.

    Args:
        metriques_test (dict): R², MAE, RMSE sur le test set.
        metriques_cv (dict): Moyenne et écart-type R² sur 5 folds.
        best_params (dict): Hyperparamètres du modèle final.
    """
    metadata = {
        "version": "1.0.0",
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


def main():
    """Point d'entrée principal du script d'entraînement."""
    print("=" * 55)
    print("  Entraînement — Modèle de Régression AssuML")
    print("=" * 55)

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
    print(f"R² moyen CV : {metriques_cv['r2_mean']:.4f} ± {metriques_cv['r2_std']:.4f}")

    # 6. Sauvegarde pipeline + metadata
    print()
    sauvegarder_pipeline(pipeline)
    sauvegarder_metadata(metriques_test, metriques_cv, BEST_PARAMS)

    print("\n✅ Entraînement terminé avec succès.")
    print("=" * 55)


if __name__ == "__main__":
    main()
