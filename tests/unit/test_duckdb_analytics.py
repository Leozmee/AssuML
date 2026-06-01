"""Tests unitaires pour big_data/duckdb_analytics.py."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from big_data.duckdb_analytics import DuckDBAnalytics

N_FIXTURE = 1_000


@pytest.fixture(scope="module")
def parquet_fixture():
    """Génère un Parquet minimal de 1 000 lignes (même schéma que le vrai dataset)."""
    rng = np.random.default_rng(0)

    fumeur = rng.choice([True, False], N_FIXTURE, p=[0.205, 0.795])
    age = rng.integers(18, 65, N_FIXTURE, dtype=np.int32)
    imc = np.round(rng.uniform(16.0, 53.0, N_FIXTURE), 2).astype(np.float32)
    enfants = rng.integers(0, 6, N_FIXTURE, dtype=np.int32)
    sexe = rng.choice(["homme", "femme"], N_FIXTURE)
    region = rng.choice(["southwest", "southeast", "northwest", "northeast"], N_FIXTURE)

    cout_predit = np.round(
        np.clip(
            256 * age
            + 339 * imc
            + 475 * enfants
            + 23800 * fumeur.astype(np.float32)
            - 12500
            + rng.normal(0, 4500, N_FIXTURE),
            1121.0,
            63770.0,
        ),
        2,
    ).astype(np.float32)

    categories = np.select(
        [cout_predit < 5000, cout_predit < 15000, cout_predit < 30000],
        ["faible", "moyen", "eleve"],
        default="critique",
    )
    decisions = np.select(
        [categories == "faible", categories == "moyen", categories == "eleve"],
        ["accepter", "accepter", "examiner"],
        default="refuser",
    )
    coeff = np.vectorize(
        {"faible": 1.0, "moyen": 1.15, "eleve": 1.35, "critique": 1.60}.get
    )(categories)
    prime = np.round(cout_predit * coeff.astype(np.float32), 2).astype(np.float32)
    centres = np.vectorize(
        {"faible": 0.15, "moyen": 0.37, "eleve": 0.63, "critique": 0.85}.get
    )(categories)
    score_risque = np.round(
        np.clip(centres.astype(np.float32) + rng.normal(0, 0.05, N_FIXTURE), 0.0, 1.0),
        4,
    ).astype(np.float32)

    tranche_age = np.select(
        [age <= 30, age <= 45, age <= 55],
        ["jeune", "adulte", "senior"],
        default="senior+",
    )
    categorie_imc = np.select(
        [imc < 18.5, imc < 25.0, imc < 30.0],
        ["sous-poids", "normal", "surpoids"],
        default="obese",
    )

    df = pd.DataFrame(
        {
            "age": age,
            "sexe": sexe,
            "imc": imc,
            "enfants": enfants,
            "fumeur": fumeur,
            "region": region,
            "cout_predit": cout_predit,
            "categorie_risque": pd.Categorical(categories),
            "decision": pd.Categorical(decisions),
            "prime": prime,
            "score_risque": score_risque,
            "cout_log": np.log1p(cout_predit).astype(np.float32),
            "tranche_age": pd.Categorical(tranche_age),
            "categorie_imc": pd.Categorical(categorie_imc),
        }
    )

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        path = f.name

    df.to_parquet(path, engine="pyarrow", index=False)
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture(scope="module")
def analytics(parquet_fixture):
    """Instance DuckDBAnalytics sur le Parquet fixture."""
    return DuckDBAnalytics(parquet_fixture)


def test_stats_par_region_shape(analytics):
    """stats_par_region() doit retourner 4 lignes (une par région)."""
    df = analytics.stats_par_region()
    assert len(df) == 4
    assert set(df.columns) == {
        "region",
        "nb",
        "cout_moy",
        "cout_med",
        "cout_std",
        "cout_min",
        "cout_max",
    }


def test_stats_par_tranche_age_shape(analytics):
    """stats_par_tranche_age() doit retourner 4 tranches."""
    df = analytics.stats_par_tranche_age()
    assert len(df) <= 4
    assert "tranche_age" in df.columns
    assert "cout_moy" in df.columns


def test_stats_par_fumeur_shape(analytics):
    """stats_par_fumeur() doit retourner 2 lignes."""
    df = analytics.stats_par_fumeur()
    assert len(df) == 2
    assert "fumeur" in df.columns
    assert "cout_moy" in df.columns
    assert "score_risque_moy" in df.columns


def test_distribution_cout_bins(analytics):
    """distribution_cout() doit retourner des bins non nuls."""
    df = analytics.distribution_cout()
    assert len(df) > 0
    assert set(df.columns) == {"bin_min", "bin_max", "nb"}
    assert (df["nb"] > 0).all()


def test_percentiles_cout_colonnes(analytics):
    """percentiles_cout() doit retourner 1 ligne avec 7 percentiles."""
    df = analytics.percentiles_cout()
    assert len(df) == 1
    for col in ["p10", "p25", "p50", "p75", "p90", "p95", "p99"]:
        assert col in df.columns
    assert df["p10"].iloc[0] <= df["p50"].iloc[0] <= df["p99"].iloc[0]


def test_correlation_age_cout_age(analytics):
    """correlation_age_cout() doit couvrir la plage 18-64."""
    df = analytics.correlation_age_cout()
    assert df["age"].min() >= 18
    assert df["age"].max() <= 64
    assert "cout_moy" in df.columns


def test_top_profils_risque_limit(analytics):
    """top_profils_risque() doit retourner au plus 10 lignes."""
    df = analytics.top_profils_risque()
    assert len(df) <= 10
    assert "score_risque_moy" in df.columns
    assert df["score_risque_moy"].is_monotonic_decreasing


def test_evolution_imc_cout(analytics):
    """evolution_imc_cout() doit retourner des bins IMC triés."""
    df = analytics.evolution_imc_cout()
    assert len(df) > 0
    assert "imc_bin" in df.columns
    assert "cout_moy" in df.columns
    assert df["imc_bin"].is_monotonic_increasing


def test_stats_globales(analytics):
    """stats_globales() doit retourner 1 ligne avec nb_total == N_FIXTURE."""
    df = analytics.stats_globales()
    assert len(df) == 1
    assert df["nb_total"].iloc[0] == N_FIXTURE
    assert 0 <= df["pct_fumeurs"].iloc[0] <= 100
    assert 18 <= df["age_moy"].iloc[0] <= 64
