"""
Script d'entraînement du modèle de classification — Niveau de Risque Assuré.

Entraîne un Pipeline GradientBoostingClassifier pour prédire la catégorie de risque
(faible / moyen / eleve / critique) à partir des features préparées.

Produit :
  - ml_models/saved_models/classification.pkl  (pipeline sérialisé, gitignored)
  - ml_models/saved_models/metadata.json       (mis à jour → v1.1.0)

Usage :
    python -m ml_models.training.train_classification            # entraînement
    python -m ml_models.training.train_classification --search    # GridSearchCV
"""

import json
import os
import sys
from datetime import date

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from dotenv import load_dotenv
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml_models.training.mlflow_gate import (
    est_meilleur_modele,
    lire_metrique_actuelle,
    promouvoir_modele,
)

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

# Hyperparamètres — historique de recherche
# ------------------------------------------
# Origine : grille GridSearchCV (cv=5, scoring='accuracy') sur
#   n_estimators=[100,200], max_depth=[3,5,None], min_samples_split=[2,5]
#   → 12 combinaisons x 5 folds, résultat retenu : (100, 3, 5).
#
# Revu le 2026-07-01 : après avoir détecté un sur-apprentissage significatif sur
# la régression (corrigé via subsample), le même diagnostic a été fait ici.
# La config (100, 3, 5) présentait un écart train-test de 0.0465 (accuracy
# train=0.9383 vs test=0.8918). Une grille élargie (rechercher_hyperparametres()
# ci-dessous, jusqu'à 432 combinaisons x 5 folds) incluant learning_rate et
# subsample a confirmé qu'ajouter learning_rate=0.05 et subsample=0.8 (en
# gardant n_estimators/max_depth/min_samples_split inchangés) réduit l'écart de
# 42% (0.0465 → 0.0269) et améliore la robustesse en CV dataset complet
# (accuracy 0.8871±0.0166 → 0.8894±0.0141), sans rien perdre sur le test set
# (accuracy=0.8918 inchangée). Adoptée.

BEST_PARAMS = {
    "n_estimators": 100,
    "max_depth": 3,
    "min_samples_split": 5,
    "learning_rate": 0.05,
    "subsample": 0.8,
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


def rechercher_hyperparametres():
    """Relance le GridSearchCV de vérification des BEST_PARAMS (essai 2026-07-01).

    Reproduit le split de main() (train_test_split, test_size=0.2, random_state=42,
    sans stratify) et explore une grille élargie autour de BEST_PARAMS, incluant
    min_samples_leaf, learning_rate et subsample — jamais testés dans la grille
    d'origine (12 combinaisons, cf. commentaire au-dessus de BEST_PARAMS).

    N'est pas appelée par main() ; à lancer explicitement via
    `python -m ml_models.training.train_classification --search`.
    """
    X, y = charger_donnees()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    preprocessor = ColumnTransformer(
        [
            ("scaler", StandardScaler(), NUMERIC_COLS),
            ("passthrough", "passthrough", PASSTHROUGH_COLS),
        ]
    )
    pipeline_gs = Pipeline(
        [
            ("preprocessor", preprocessor),
            ("model", GradientBoostingClassifier(random_state=RANDOM_STATE)),
        ]
    )

    param_grid = {
        "model__n_estimators": [100, 150, 200],
        "model__max_depth": [2, 3],
        "model__min_samples_split": [2, 5, 10],
        "model__min_samples_leaf": [1, 2],
        "model__learning_rate": [0.05, 0.1, 0.2],
        "model__subsample": [0.7, 0.8, 0.9, 1.0],
    }
    n_combos = 1
    for valeurs in param_grid.values():
        n_combos *= len(valeurs)
    print(f"Grille : {n_combos} combinaisons x 5 folds = {n_combos * 5} fits")

    grid_search = GridSearchCV(
        pipeline_gs, param_grid, cv=5, scoring="f1_macro", n_jobs=-1, verbose=1
    )
    grid_search.fit(X_train, y_train)

    print(f"\n✅ Meilleurs hyperparamètres : {grid_search.best_params_}")
    print(f"   f1_macro CV moyen (train) : {grid_search.best_score_:.4f}")

    y_pred_gs = grid_search.best_estimator_.predict(X_test)
    metriques_gs = calculer_metriques_clf(y_test, y_pred_gs)
    print("\n--- Métriques test (candidat GridSearchCV) ---")
    print(f"Accuracy  : {metriques_gs['accuracy']:.4f}")
    print(f"F1-macro  : {metriques_gs['f1_macro']:.4f}")

    baseline = construire_pipeline()
    baseline.fit(X_train, y_train)
    metriques_baseline = calculer_metriques_clf(y_test, baseline.predict(X_test))
    print("\n--- Métriques test (BEST_PARAMS actuels) ---")
    print(f"Accuracy  : {metriques_baseline['accuracy']:.4f}")
    print(f"F1-macro  : {metriques_baseline['f1_macro']:.4f}")


def main():
    """Entraîne le modèle de classification et sérialise le pipeline."""
    print("=" * 60)
    print("Entraînement du modèle de classification — AssuML")
    print("=" * 60)

    load_dotenv()
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow.set_experiment("assuml-classification")

    with mlflow.start_run():
        mlflow.sklearn.autolog()

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

        # Logging explicite MLflow (params + métriques, complète l'autolog)
        mlflow.log_params(BEST_PARAMS)
        for cle, valeur in {**metriques_test, **metriques_cv}.items():
            mlflow.log_metric(cle, valeur)

        # Gate anti-régression : ne déployer que si strictement meilleur
        metrique_actuelle = lire_metrique_actuelle(
            METADATA_PATH, "classification", "accuracy"
        )
        if est_meilleur_modele(metriques_test["accuracy"], metrique_actuelle):
            os.makedirs(os.path.abspath(MODEL_DIR), exist_ok=True)
            chemin_clf = os.path.abspath(CLF_PATH)
            joblib.dump(pipeline, chemin_clf)
            print("✅ classification.pkl sauvegardé")

            mettre_a_jour_metadata(metriques_test, metriques_cv, BEST_PARAMS)

            logged_model = mlflow.last_logged_model()
            promouvoir_modele("assuml-classification", logged_model.model_id)
        else:
            print(
                f"\n⚠️  Modèle non déployé — accuracy={metriques_test['accuracy']:.4f} "
                f"≤ accuracy actuelle={metrique_actuelle:.4f}. "
                "classification.pkl conservé, run tracké dans MLflow."
            )

    print("\n" + "=" * 60)
    print("Entraînement terminé avec succès.")
    print("=" * 60)


if __name__ == "__main__":
    if "--search" in sys.argv:
        rechercher_hyperparametres()
    else:
        main()
