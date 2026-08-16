"""
Script de génération du dataset synthétique Big Data.

Lit data/small_data/insurance.csv (1 338 lignes) pour extraire les
distributions statistiques réelles, puis génère 5 000 000 de lignes
synthétiques et les sauvegarde dans data/big_data/insurance_big.parquet.

Usage :
    python big_data/generate_synthetic.py

Colonnes générées (14) :
    Bloc clients   : age, sexe, imc, enfants, fumeur, region
    Bloc prédiction: cout_predit, categorie_risque, decision, prime, score_risque
    Features       : cout_log, tranche_age, categorie_imc
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd

# ── Paramètres globaux ────────────────────────────────────────────────────────

N_LIGNES = 5_000_000

# Graine fixe : relancer le script deux fois produit exactement le même fichier
SEED = 42

CHEMIN_CSV = Path("data/small_data/insurance.csv")
CHEMIN_PARQUET = Path("data/big_data/insurance_big.parquet")

# Min/max de charges dans le vrai dataset Kaggle — on clippera nos valeurs dans
# ces bornes pour que le synthétique reste réaliste
COUT_MIN = 1121.0
COUT_MAX = 63770.0


# ── Étape 1 : extraction des distributions réelles ───────────────────────────


def extraire_distributions(df: pd.DataFrame) -> dict:
    """Extrait les distributions statistiques du CSV source.

    Pour age on retient moyenne + écart-type globaux (distribution normale).
    Pour les variables catégorielles (enfants, sexe, region) on retient les
    valeurs brutes : np.random.choice les tirera en respectant les fréquences
    exactes du vrai dataset plutôt qu'une proportion théorique.

    imc et fumeur sont calculés PAR RÉGION (et non globalement) : le vrai
    dataset montre un écart régional réel (ex. southeast a un IMC moyen et
    un taux de tabagisme nettement plus élevés que les 3 autres régions) —
    une distribution globale unique effacerait cet écart dans le synthétique.
    """
    dist_par_region = {}
    for region in df["region"].unique():
        sous_df = df[df["region"] == region]
        dist_par_region[region] = {
            "imc_moy": sous_df["bmi"].mean(),
            "imc_std": sous_df["bmi"].std(),
            "fumeur_vals": (sous_df["smoker"] == "yes").values,
        }

    return {
        # Loi normale : age ~ N(moy, std), clippé ensuite entre 18 et 64
        "age_moy": df["age"].mean(),
        "age_std": df["age"].std(),
        # Tirage avec remise depuis les valeurs réelles → fréquences automatiques
        "enfants_vals": df["children"].values,
        # Conversion male/female → homme/femme (convention BDD française)
        "sexe_vals": df["sex"].map({"male": "homme", "female": "femme"}).values,
        "region_vals": df["region"].values,
        # Distributions imc/fumeur indexées par région (cf. docstring)
        "dist_par_region": dist_par_region,
    }


# ── Étape 2 : colonnes clients ────────────────────────────────────────────────


def generer_colonnes_clients(dist: dict, rng: np.random.Generator) -> dict:
    """Génère les 6 colonnes du bloc clients à partir des distributions CSV.

    Toutes les opérations sont vectorisées (pas de boucle Python) :
    NumPy génère les 5M valeurs d'un coup, ce qui est ~100x plus rapide
    qu'un appel ligne par ligne. region est générée en premier ; imc et
    fumeur sont ensuite tirés PAR SOUS-GROUPE RÉGION (masques booléens,
    4 groupes — toujours vectorisé, pas de boucle ligne par ligne) pour
    reproduire l'écart régional réel du dataset source (cf.
    extraire_distributions).
    """
    print("  Génération colonnes clients...")

    # np.clip évite les ages aberrants que la loi normale pourrait générer
    # (ex : -3 ans ou 120 ans hors du domaine assuré)
    age = rng.normal(dist["age_moy"], dist["age_std"], N_LIGNES)
    age = np.clip(age, 18, 64).astype(np.int32)

    # np.random.choice tire avec remise depuis le tableau de valeurs réelles :
    # si le CSV a 427 lignes "0 enfant" sur 1338, la probabilité de tirer 0
    # sera automatiquement 427/1338 ≈ 31.9% — pas besoin de hardcoder les %
    enfants = rng.choice(dist["enfants_vals"], N_LIGNES).astype(np.int32)
    sexe = rng.choice(dist["sexe_vals"], N_LIGNES)
    region = rng.choice(dist["region_vals"], N_LIGNES)

    imc = np.empty(N_LIGNES, dtype=np.float32)
    fumeur = np.empty(N_LIGNES, dtype=bool)
    for nom_region, dist_region in dist["dist_par_region"].items():
        masque = region == nom_region
        n_region = int(masque.sum())
        imc[masque] = rng.normal(
            dist_region["imc_moy"], dist_region["imc_std"], n_region
        )
        fumeur[masque] = rng.choice(dist_region["fumeur_vals"], n_region)
    imc = np.round(np.clip(imc, 15.96, 53.13), 2).astype(np.float32)

    return {
        "age": age,
        "sexe": sexe,
        "imc": imc,
        "enfants": enfants,
        "fumeur": fumeur,
        "region": region,
    }


# ── Étape 3 : coût prédit ─────────────────────────────────────────────────────


def generer_cout_predit(cols: dict, rng: np.random.Generator) -> np.ndarray:
    """Génère cout_predit avec une formule linéaire calibrée sur le vrai dataset.

    Les coefficients (256, 339, 475, 23800, -130) sont les poids approximatifs
    d'une régression linéaire entraînée sur insurance.csv. Ils reproduisent les
    corrélations réelles : un fumeur coûte ~23 800 $ de plus qu'un non-fumeur,
    chaque année d'âge ajoute ~256 $, etc.

    Le bruit gaussien (std=4500) représente la variabilité individuelle non
    expliquée par le modèle linéaire (génétique, historique médical...).
    Sans ce bruit, tous les profils identiques auraient exactement le même coût.
    """
    print("  Génération cout_predit (formule calibrée)...")

    # Conversion booléen → 0/1 pour pouvoir multiplier dans la formule
    fumeur_flag = cols["fumeur"].astype(np.float32)
    sexe_femme_flag = (cols["sexe"] == "femme").astype(np.float32)

    # Bruit aléatoire : déviation individuelle autour de la valeur théorique
    bruit = rng.normal(0, 4500, N_LIGNES)

    cout_brut = (
        256 * cols["age"]  # +256 $ par année d'âge
        + 339 * cols["imc"]  # +339 $ par point d'IMC
        + 475 * cols["enfants"]  # +475 $ par enfant
        + 23800 * fumeur_flag  # +23 800 $ si fumeur (facteur de risque majeur)
        - 130 * sexe_femme_flag  # légèrement moins élevé pour les femmes
        - 12500  # constante (ordonnée à l'origine)
        + bruit
    )

    # np.clip garantit qu'aucune valeur ne sort des bornes du vrai dataset
    return np.round(np.clip(cout_brut, COUT_MIN, COUT_MAX), 2).astype(np.float32)


# ── Étape 4 : colonnes prédiction ────────────────────────────────────────────


def generer_colonnes_prediction(  # noqa: E501
    cout_predit: np.ndarray, rng: np.random.Generator
) -> dict:
    """Génère les 5 colonnes du bloc prédiction à partir de cout_predit.

    On reproduit ici la logique de business/risk_engine.py et business/scoring.py
    mais en version vectorisée (np.select au lieu de boucles) pour traiter
    5 millions de lignes en quelques secondes.
    """
    print("  Génération colonnes prédiction (business logic)...")

    # np.select est l'équivalent vectorisé d'un if/elif/else :
    # il évalue chaque condition sur tout le tableau et retourne le résultat
    # correspondant pour chaque ligne — même logique que get_categorie_risque()
    conditions = [
        cout_predit < 5_000,
        (cout_predit >= 5_000) & (cout_predit < 15_000),
        (cout_predit >= 15_000) & (cout_predit < 30_000),
    ]
    categories = np.select(
        conditions,
        ["faible", "moyen", "eleve"],
        default="critique",  # toutes les lignes restantes (≥ 30 000)
    )

    # Même logique que get_decision() — mapping catégorie → décision de souscription
    decisions = np.select(
        [categories == "faible", categories == "moyen", categories == "eleve"],
        ["accepter", "accepter", "examiner"],
        default="refuser",
    )

    # np.vectorize applique un dictionnaire comme une fonction scalaire sur
    # chaque élément du tableau — équivalent de [coefficients[c] for c in categories]
    # mais sans boucle Python explicite
    coefficients = {"faible": 1.0, "moyen": 1.15, "eleve": 1.35, "critique": 1.60}
    coeff_array = np.vectorize(coefficients.get)(categories).astype(np.float32)
    prime = np.round(cout_predit * coeff_array, 2).astype(np.float32)

    # score_risque [0,1] : probabilité simulée par catégorie avec un bruit léger
    # Exemple : catégorie "eleve" → centre 0.63, bruit ±0.05 → score entre ~0.50 et 0.75
    # np.clip garantit que le score reste dans [0, 1] même avec le bruit
    centres = {"faible": 0.15, "moyen": 0.37, "eleve": 0.63, "critique": 0.85}
    centre_array = np.vectorize(centres.get)(categories).astype(np.float32)
    bruit_score = rng.normal(0, 0.05, N_LIGNES).astype(np.float32)
    score_risque = np.round(np.clip(centre_array + bruit_score, 0.0, 1.0), 4).astype(
        np.float32
    )

    return {
        "cout_predit": cout_predit,
        "categorie_risque": categories,
        "decision": decisions,
        "prime": prime,
        "score_risque": score_risque,
    }


# ── Étape 5 : features engineered ────────────────────────────────────────────


def generer_features_engineered(cols: dict) -> dict:
    """Calcule les 3 colonnes analytiques dérivées des autres colonnes.

    Ces colonnes n'existent pas dans la BDD — elles sont ajoutées directement
    dans le Parquet pour éviter de les recalculer à chaque requête DuckDB.
    """
    print("  Calcul features engineered...")

    # log1p(x) = log(1 + x) : transforme la distribution asymétrique des coûts
    # (longue queue à droite) en distribution plus proche d'une loi normale,
    # utile pour certaines analyses statistiques
    cout_log = np.log1p(cols["cout_predit"]).astype(np.float32)

    # Segmentation de l'âge en 4 tranches métier (même logique qu'en SAS/SQL)
    # np.select teste les conditions dans l'ordre → le premier True gagne
    tranche_age = np.select(
        [cols["age"] <= 30, cols["age"] <= 45, cols["age"] <= 55],
        ["jeune", "adulte", "senior"],
        default="senior+",  # age > 55
    )

    # Catégories IMC selon les seuils de l'OMS (Organisation Mondiale de la Santé)
    categorie_imc = np.select(
        [cols["imc"] < 18.5, cols["imc"] < 25.0, cols["imc"] < 30.0],
        ["sous-poids", "normal", "surpoids"],
        default="obese",  # imc >= 30
    )

    return {
        "cout_log": cout_log,
        "tranche_age": tranche_age,
        "categorie_imc": categorie_imc,
    }


# ── Point d'entrée ────────────────────────────────────────────────────────────


def main():
    """Point d'entrée principal du script de génération."""
    debut = time.time()

    print(f"Génération de {N_LIGNES:,} lignes synthétiques (seed={SEED})...")
    print(f"Source : {CHEMIN_CSV}")

    # Créer data/big_data/ s'il n'existe pas encore
    CHEMIN_PARQUET.parent.mkdir(parents=True, exist_ok=True)

    # [1/5] Lire le vrai CSV et extraire ses distributions statistiques
    print("\n[1/5] Lecture et analyse du CSV source...")
    df_source = pd.read_csv(CHEMIN_CSV)
    dist = extraire_distributions(df_source)
    print(f"      {len(df_source)} lignes lues, distributions extraites.")

    # Initialiser le générateur avec une graine fixe pour la reproductibilité
    # np.random.default_rng est l'API moderne de NumPy (remplace np.random.seed)
    rng = np.random.default_rng(SEED)

    # [2/5] Colonnes clients : age, sexe, imc, enfants, fumeur, region
    print("\n[2/5] Colonnes clients (age, sexe, imc, enfants, fumeur, region)...")
    cols = generer_colonnes_clients(dist, rng)

    # [3/5] Coût prédit : formule linéaire calibrée + bruit gaussien
    print("\n[3/5] Coût prédit (formule linéaire calibrée)...")
    cout_predit = generer_cout_predit(cols, rng)

    # [4/5] Colonnes prédiction dérivées de cout_predit
    print("\n[4/5] Colonnes prédiction...")  # categorie_risque, decision, prime
    cols_pred = generer_colonnes_prediction(cout_predit, rng)
    cols.update(cols_pred)  # fusionne les deux dicts

    # [5/5] Features engineered + sauvegarde
    print("\n[5/5] Features engineered et sauvegarde Parquet...")
    cols.update(generer_features_engineered(cols))

    # Assemblage final : dict de tableaux NumPy → DataFrame Pandas
    df = pd.DataFrame(cols)

    # Convertir les colonnes texte en "category" : réduit la mémoire ~10x
    # (stocke une seule fois chaque valeur unique + un tableau d'indices)
    cols_cat = [
        "sexe",
        "region",
        "categorie_risque",
        "decision",
        "tranche_age",
        "categorie_imc",
    ]
    for col in cols_cat:
        df[col] = df[col].astype("category")

    # Sauvegarde en Parquet avec PyArrow (format colonne, compression Snappy)
    # index=False : ne pas écrire l'index Pandas (0, 1, 2...) dans le fichier
    df.to_parquet(CHEMIN_PARQUET, engine="pyarrow", index=False)

    duree = time.time() - debut
    taille_mo = CHEMIN_PARQUET.stat().st_size / (1024 * 1024)

    print(f"\n✅ Parquet généré : {CHEMIN_PARQUET}")
    print(f"   Lignes      : {len(df):,}")
    print(f"   Colonnes    : {len(df.columns)} {list(df.columns)}")
    print(f"   Taille      : {taille_mo:.1f} Mo")
    print(f"   Durée       : {duree:.1f}s")


if __name__ == "__main__":
    main()
