"""Tests unitaires pour big_data/generate_synthetic.py."""

import os

import pandas as pd
import pytest

CHEMIN_PARQUET = "data/big_data/insurance_big.parquet"

# insurance_big.parquet est gitignored (5M lignes générées localement, jamais
# commité) : ces tests nécessitent le fichier généré et sont ignorés si absent
# (ex: CI), cf. constitution Principe IV.
requires_parquet = pytest.mark.skipif(
    not os.path.exists(CHEMIN_PARQUET),
    reason="insurance_big.parquet absent (non généré dans cet environnement)",
)

COLONNES_ATTENDUES = [
    "age",
    "sexe",
    "imc",
    "enfants",
    "fumeur",
    "region",
    "cout_predit",
    "categorie_risque",
    "decision",
    "prime",
    "score_risque",
    "cout_log",
    "tranche_age",
    "categorie_imc",
]


@pytest.fixture(scope="module")
def df():
    """Charge le Parquet une seule fois pour tous les tests."""
    return pd.read_parquet(CHEMIN_PARQUET)


@requires_parquet
def test_nombre_lignes(df):
    """Le Parquet doit contenir exactement 5 000 000 lignes."""
    assert len(df) == 5_000_000


@requires_parquet
def test_colonnes(df):
    """Les 14 colonnes attendues doivent toutes être présentes."""
    assert list(df.columns) == COLONNES_ATTENDUES


@requires_parquet
def test_age_bornes(df):
    """age doit être compris entre 18 et 64."""
    assert df["age"].min() >= 18
    assert df["age"].max() <= 64


@requires_parquet
def test_imc_bornes(df):
    """imc doit être compris entre 15.96 et 53.13."""
    assert df["imc"].min() >= 15.96
    assert df["imc"].max() <= 53.13


@requires_parquet
def test_cout_predit_bornes(df):
    """cout_predit doit être compris entre 1121 et 63770."""
    assert df["cout_predit"].min() >= 1121.0
    assert df["cout_predit"].max() <= 63770.0


@requires_parquet
def test_fumeur_booleen(df):
    """fumeur doit contenir uniquement True ou False."""
    assert set(df["fumeur"].unique()).issubset({True, False})


@requires_parquet
def test_score_risque_bornes(df):
    """score_risque doit être compris entre 0 et 1."""
    assert df["score_risque"].min() >= 0.0
    assert df["score_risque"].max() <= 1.0


@requires_parquet
def test_sexe_valeurs(df):
    """sexe doit contenir uniquement homme ou femme."""
    assert set(df["sexe"].cat.categories).issubset({"homme", "femme"})


@requires_parquet
def test_categorie_risque_valeurs(df):
    """categorie_risque doit contenir les 4 catégories attendues."""
    cats = set(df["categorie_risque"].cat.categories)
    assert cats.issubset({"faible", "moyen", "eleve", "critique"})


@requires_parquet
def test_decision_valeurs(df):
    """decision doit contenir uniquement accepter, examiner ou refuser."""
    decisions = set(df["decision"].cat.categories)
    assert decisions.issubset({"accepter", "examiner", "refuser"})


@requires_parquet
def test_proportion_fumeurs(df):
    """La proportion de fumeurs doit être proche de 20.5% (±3%)."""
    pct = df["fumeur"].mean()
    assert 0.175 <= pct <= 0.235


@requires_parquet
def test_cout_log_coherent(df):
    """cout_log doit être égal à log1p(cout_predit)."""
    import numpy as np

    diff = (df["cout_log"] - np.log1p(df["cout_predit"])).abs().max()
    assert diff < 0.001


@requires_parquet
def test_variation_regionale_imc(df):
    """L'IMC moyen doit varier significativement selon la région (feature
    016-bdd-externe-regional — imc/fumeur sont désormais tirés par région,
    reproduisant l'écart réel du dataset source, ex. southeast ~33 vs
    ~29-30 pour les autres régions)."""
    imc_par_region = df.groupby("region", observed=True)["imc"].mean()
    ecart = imc_par_region.max() - imc_par_region.min()
    assert ecart > 2.0


@requires_parquet
def test_variation_regionale_fumeur(df):
    """Le taux de fumeurs doit varier significativement selon la région
    (même logique que test_variation_regionale_imc)."""
    taux_par_region = df.groupby("region", observed=True)["fumeur"].mean() * 100
    ecart = taux_par_region.max() - taux_par_region.min()
    assert ecart > 3.0


def test_reproductibilite_seed():
    """Deux exécutions avec le même SEED doivent produire des colonnes
    clients strictement identiques (génération corrélée par région
    comprise)."""
    import numpy as np
    import pandas as pd

    import big_data.generate_synthetic as gs

    n_lignes_original = gs.N_LIGNES
    gs.N_LIGNES = 10_000
    try:
        df_source = pd.read_csv(gs.CHEMIN_CSV)
        dist = gs.extraire_distributions(df_source)

        cols_1 = gs.generer_colonnes_clients(dist, np.random.default_rng(gs.SEED))
        cols_2 = gs.generer_colonnes_clients(dist, np.random.default_rng(gs.SEED))

        for cle in cols_1:
            np.testing.assert_array_equal(cols_1[cle], cols_2[cle])
    finally:
        gs.N_LIGNES = n_lignes_original
