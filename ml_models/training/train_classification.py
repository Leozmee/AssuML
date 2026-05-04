"""
Script d'entraînement du modèle de classification — Niveau de Risque Assuré.

Entraîne un Pipeline GradientBoostingClassifier pour prédire la catégorie de risque
(faible / moyen / eleve / critique) à partir des features préparées.

Produit :
  - ml_models/saved_models/classification.pkl  (pipeline sérialisé, gitignored)
  - ml_models/saved_models/metadata.json       (mis à jour → v1.1.0)

Usage :
    python -m ml_models.training.train_classification
"""

import json
import os
from datetime import date

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ── Chemins ────────────────────────────────────────────────────────────────
_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(_DIR, "..", "..", "data", "processed", "features.csv")
MODEL_DIR = os.path.join(_DIR, "..", "saved_models")
CLF_PATH = os.path.join(MODEL_DIR, "classification.pkl")
METADATA_PATH = os.path.join(MODEL_DIR, "metadata.json")

# ── Constantes ─────────────────────────────────────────────────────────────
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
TARGET_CLF = "categorie_risque"
NUMERIC_COLS = ["age", "imc", "enfants"]
PASSTHROUGH_COLS = [
    "sexe",
    "fumeur",
    "region_northwest",
    "region_southeast",
    "region_southwest",
]
CLASSES_ORDER = ["faible", "moyen", "eleve", "critique"]
RANDOM_STATE = 42

# Hyperparamètres optimaux issus de GridSearchCV (notebook 03, Section 10)
BEST_PARAMS = {
    "n_estimators": 100,
    "max_depth": 3,
    "min_samples_split": 5,
}


# ── Fonctions ──────────────────────────────────────────────────────────────


def charger_donnees():
    """Charge le dataset de features préparé par la feature 002.

    Returns:
        tuple[pd.DataFrame, pd.Series]: (X, y) — features et target classification.

    Raises:
        FileNotFoundError: Si features.csv est absent.
    """
    chemin_abs = os.path.abspath(DATA_PATH)
    if not os.path.exists(chemin_abs):
        raise FileNotFoundError(
            f"Dataset introuvable : {chemin_abs}\n"
            "Exécuter d'abord : notebooks/02_feature_engineering.ipynb"
        )
    df = pd.read_csv(chemin_abs)
    X = df[FEATURE_COLS]
    y = df[TARGET_CLF]
    print(f"✅ Dataset chargé : {len(df)} lignes, {len(FEATURE_COLS)} features")
    return X, y


def construire_pipeline():
    """Construit le Pipeline sklearn avec le même ColumnTransformer que la régression.

    Le preprocesseur applique :
      - StandardScaler sur les variables numériques (age, imc, enfants)
      - passthrough sur les variables binaires/one-hot

    Returns:
        Pipeline: Pipeline non encore entraîné.
    """
    preprocessor = ColumnTransformer(
        [
            ("scaler", StandardScaler(), NUMERIC_COLS),
            ("passthrough", "passthrough", PASSTHROUGH_COLS),
        ]
    )
    clf = GradientBoostingClassifier(
        **BEST_PARAMS,
        random_state=RANDOM_STATE,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", clf)])


def calculer_metriques_clf(y_true, y_pred):
    """Calcule les métriques de classification à partir des prédictions.

    Args:
        y_true: Labels réels.
        y_pred: Labels prédits par le modèle.

    Returns:
        dict: accuracy, f1_macro, precision_macro, recall_macro (arrondis 4 décimales).
    """
    rapport = classification_report(y_true, y_pred, output_dict=True)
    return {
        "accuracy": round(rapport["accuracy"], 4),
        "f1_macro": round(rapport["macro avg"]["f1-score"], 4),
        "precision_macro": round(rapport["macro avg"]["precision"], 4),
        "recall_macro": round(rapport["macro avg"]["recall"], 4),
    }


def mettre_a_jour_metadata(metriques_test, metriques_cv, best_params):
    """Met à jour metadata.json — ajoute la section classification, passe à v1.1.0.

    Lit le fichier existant (v1.0.0), restructure la clé régression si nécessaire,
    ajoute la clé classification, incrémente la version globale à 1.1.0.

    Args:
        metriques_test (dict): Métriques sur le test set (accuracy, f1_macro, ...).
        metriques_cv (dict): Métriques cross-validation (accuracy_mean, accuracy_std).
        best_params (dict): Hyperparamètres du meilleur modèle.
    """
    chemin_abs = os.path.abspath(METADATA_PATH)
    with open(chemin_abs) as f:
        meta = json.load(f)

    # ── Restructuration : migration v1.0.0 (flat) → v1.1.0 (nested) ──────
    if "regression" not in meta:
        meta_regression = {
            "version": "1.0.0",
            "date_entrainement": meta.get("date_entrainement", ""),
            "algorithme": meta.get("algorithme", "GradientBoostingRegressor"),
            "hyperparametres": meta.get("hyperparametres", {}),
            "metriques_test": meta.get("metriques_test", {}),
            "metriques_cv": meta.get("metriques_cv", {}),
        }
        # Nettoyage des clés dupliquées au niveau racine
        for cle in [
            "date_entrainement",
            "algorithme",
            "hyperparametres",
            "metriques_test",
            "metriques_cv",
            "target",
        ]:
            meta.pop(cle, None)
        meta["regression"] = meta_regression

    # ── Ajout de la section classification ────────────────────────────────
    meta["classification"] = {
        "version": "1.0.0",
        "date_entrainement": date.today().isoformat(),
        "algorithme": "GradientBoostingClassifier",
        "hyperparametres": best_params,
        "metriques_test": metriques_test,
        "metriques_cv": metriques_cv,
    }

    # ── Mise à jour des métadonnées globales ─────────────────────────────
    meta["version"] = "1.1.0"
    meta["date_mise_a_jour"] = date.today().isoformat()
    meta["target_regression"] = "charges"
    meta["target_classification"] = TARGET_CLF

    with open(chemin_abs, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("✅ metadata.json mis à jour → v1.1.0")


def main():
    """Entraîne le modèle de classification et sérialise le pipeline."""
    print("=" * 60)
    print("Entraînement du modèle de classification — AssuML")
    print("=" * 60)

    # Chargement
    X, y = charger_donnees()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    # Entraînement
    pipeline = construire_pipeline()
    pipeline.fit(X_train, y_train)

    # Métriques test
    y_pred = pipeline.predict(X_test)
    metriques_test = calculer_metriques_clf(y_test, y_pred)

    print("\n--- Métriques finales (GradientBoostingClassifier) ---")
    print(f"Accuracy  : {metriques_test['accuracy']:.4f}")
    print(f"F1-macro  : {metriques_test['f1_macro']:.4f}")
    print(f"Precision : {metriques_test['precision_macro']:.4f}")
    print(f"Recall    : {metriques_test['recall_macro']:.4f}")

    # Cross-validation 5 plis
    cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy", n_jobs=-1)
    metriques_cv = {
        "accuracy_mean": round(float(cv_scores.mean()), 4),
        "accuracy_std": round(float(cv_scores.std()), 4),
    }
    print(f"\nCV accuracy : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Sérialisation
    os.makedirs(os.path.abspath(MODEL_DIR), exist_ok=True)
    chemin_clf = os.path.abspath(CLF_PATH)
    joblib.dump(pipeline, chemin_clf)
    print("✅ classification.pkl sauvegardé")

    # Mise à jour metadata.json
    mettre_a_jour_metadata(metriques_test, metriques_cv, BEST_PARAMS)

    print("\n" + "=" * 60)
    print("Entraînement terminé avec succès.")
    print("Version metadata.json : 1.1.0")
    print("=" * 60)


if __name__ == "__main__":
    main()
