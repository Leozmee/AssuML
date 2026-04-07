"""Tests unitaires pour data_pipeline/transform/normalization.py."""
import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from data_pipeline.transform.normalization import encode_categoricals


@pytest.fixture
def df_francais():
    """DataFrame avec nommage français (après rename_columns) — 4 régions présentes."""
    return pd.DataFrame({
        'age': [25, 35, 45, 50],
        'sexe': ['female', 'male', 'female', 'male'],
        'imc': [22.5, 30.0, 27.3, 33.0],
        'enfants': [0, 2, 1, 0],
        'fumeur': ['yes', 'no', 'no', 'yes'],
        'region': ['southwest', 'northeast', 'southeast', 'northwest'],
        'charges': [16884.0, 4000.0, 8000.0, 20000.0],
    })


@pytest.fixture
def df_avec_labels_fr():
    """DataFrame avec labels français (femme/homme, oui/non)."""
    return pd.DataFrame({
        'sexe': ['femme', 'homme', 'femme'],
        'fumeur': ['oui', 'non', 'non'],
        'region': ['southwest', 'northeast', 'southeast'],
        'charges': [16884.0, 4000.0, 8000.0],
    })


# --- Tests encodage sexe ---

def test_encode_sexe_femme_est_1(df_francais):
    """female ou femme doit être encodé en 1."""
    result = encode_categoricals(df_francais)
    assert result['sexe'].iloc[0] == 1  # female
    assert result['sexe'].iloc[2] == 1  # female


def test_encode_sexe_homme_est_0(df_francais):
    """male ou homme doit être encodé en 0."""
    result = encode_categoricals(df_francais)
    assert result['sexe'].iloc[1] == 0  # male


def test_encode_labels_francais_sexe(df_avec_labels_fr):
    """Les labels français (femme/homme) doivent aussi être encodés."""
    result = encode_categoricals(df_avec_labels_fr)
    assert result['sexe'].iloc[0] == 1   # femme
    assert result['sexe'].iloc[1] == 0   # homme


def test_sexe_est_entier(df_francais):
    """La colonne sexe encodée doit être de type entier."""
    result = encode_categoricals(df_francais)
    assert result['sexe'].dtype in [int, 'int64', 'int32']


# --- Tests encodage fumeur ---

def test_encode_fumeur_yes_est_1(df_francais):
    """yes/oui doit être encodé en 1."""
    result = encode_categoricals(df_francais)
    assert result['fumeur'].iloc[0] == 1  # yes


def test_encode_fumeur_no_est_0(df_francais):
    """no/non doit être encodé en 0."""
    result = encode_categoricals(df_francais)
    assert result['fumeur'].iloc[1] == 0  # no
    assert result['fumeur'].iloc[2] == 0  # no


def test_encode_labels_francais_fumeur(df_avec_labels_fr):
    """Les labels français (oui/non) doivent aussi être encodés."""
    result = encode_categoricals(df_avec_labels_fr)
    assert result['fumeur'].iloc[0] == 1   # oui
    assert result['fumeur'].iloc[1] == 0   # non


# --- Tests one-hot region ---

def test_region_northeast_supprimee(df_francais):
    """La colonne region_northeast doit être supprimée (référence drop_first)."""
    result = encode_categoricals(df_francais)
    assert 'region_northeast' not in result.columns
    assert 'region' not in result.columns


def test_region_colonnes_presentes(df_francais):
    """Les colonnes region_northwest, region_southeast, region_southwest doivent être présentes."""
    result = encode_categoricals(df_francais)
    for col in ['region_northwest', 'region_southeast', 'region_southwest']:
        assert col in result.columns, f"{col} manquante"


def test_region_valeurs_binaires(df_francais):
    """Les colonnes one-hot doivent contenir uniquement 0 et 1."""
    result = encode_categoricals(df_francais)
    for col in ['region_northwest', 'region_southeast', 'region_southwest']:
        assert result[col].isin([0, 1]).all()


def test_region_northeast_encode_comme_000(df_francais):
    """Un client northeast doit avoir toutes les colonnes region à 0."""
    result = encode_categoricals(df_francais)
    # La 2e ligne (index 1) est northeast — toutes les colonnes region doivent être 0
    row_northeast = result.iloc[1]
    region_cols = [c for c in result.columns if c.startswith('region_')]
    for col in region_cols:
        assert row_northeast[col] == 0, f"{col} devrait être 0 pour northeast"


# --- Tests généraux ---

def test_non_destructif(df_francais):
    """La fonction ne doit pas modifier le DataFrame original."""
    original = df_francais.copy()
    encode_categoricals(df_francais)
    pd.testing.assert_frame_equal(df_francais, original)


def test_colonnes_non_categoriques_preservees(df_francais):
    """age, imc, enfants, charges doivent être conservées telles quelles."""
    result = encode_categoricals(df_francais)
    for col in ['age', 'imc', 'enfants', 'charges']:
        assert col in result.columns
        pd.testing.assert_series_equal(result[col], df_francais[col])


def test_dataset_complet():
    """Test sur le vrai dataset si disponible."""
    csv_path = 'insurance.csv'
    if not os.path.exists(csv_path):
        pytest.skip("insurance.csv non trouvé à la racine")
    from data_pipeline.transform.cleaning import rename_columns
    df = pd.read_csv(csv_path)
    df = rename_columns(df)
    result = encode_categoricals(df)
    assert result['sexe'].isin([0, 1]).all()
    assert result['fumeur'].isin([0, 1]).all()
    assert 'region_northeast' not in result.columns
    assert result.shape[0] == 1338
