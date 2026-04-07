"""Tests unitaires pour data_pipeline/transform/cleaning.py."""
import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from data_pipeline.transform.cleaning import rename_columns


@pytest.fixture
def df_kaggle():
    """DataFrame synthétique au format Kaggle (3 lignes)."""
    return pd.DataFrame({
        'age': [25, 35, 45],
        'sex': ['female', 'male', 'female'],
        'bmi': [22.5, 30.0, 27.3],
        'children': [0, 2, 1],
        'smoker': ['yes', 'no', 'no'],
        'region': ['southwest', 'northeast', 'southeast'],
        'charges': [16884.0, 4000.0, 8000.0],
    })


def test_rename_sex_to_sexe(df_kaggle):
    """sex doit être renommé en sexe."""
    result = rename_columns(df_kaggle)
    assert 'sexe' in result.columns
    assert 'sex' not in result.columns


def test_rename_bmi_to_imc(df_kaggle):
    """bmi doit être renommé en imc."""
    result = rename_columns(df_kaggle)
    assert 'imc' in result.columns
    assert 'bmi' not in result.columns


def test_rename_children_to_enfants(df_kaggle):
    """children doit être renommé en enfants."""
    result = rename_columns(df_kaggle)
    assert 'enfants' in result.columns
    assert 'children' not in result.columns


def test_rename_smoker_to_fumeur(df_kaggle):
    """smoker doit être renommé en fumeur."""
    result = rename_columns(df_kaggle)
    assert 'fumeur' in result.columns
    assert 'smoker' not in result.columns


def test_colonnes_inchangees(df_kaggle):
    """age, region et charges ne doivent pas être renommés."""
    result = rename_columns(df_kaggle)
    for col in ['age', 'region', 'charges']:
        assert col in result.columns


def test_valeurs_preservees(df_kaggle):
    """Les valeurs des colonnes ne doivent pas être modifiées."""
    result = rename_columns(df_kaggle)
    assert list(result['imc']) == [22.5, 30.0, 27.3]
    assert list(result['enfants']) == [0, 2, 1]
    assert list(result['fumeur']) == ['yes', 'no', 'no']


def test_non_destructif(df_kaggle):
    """La fonction ne doit pas modifier le DataFrame original."""
    original_cols = list(df_kaggle.columns)
    rename_columns(df_kaggle)
    assert list(df_kaggle.columns) == original_cols


def test_sous_ensemble(df_kaggle):
    """La fonction doit fonctionner sur un sous-ensemble de lignes."""
    subset = df_kaggle.iloc[:1]
    result = rename_columns(subset)
    assert result.shape == (1, 7)
    assert 'sexe' in result.columns


def test_dataset_complet():
    """Test sur le vrai dataset si disponible."""
    csv_path = 'insurance.csv'
    if not os.path.exists(csv_path):
        pytest.skip("insurance.csv non trouvé à la racine")
    df = pd.read_csv(csv_path)
    result = rename_columns(df)
    assert result.shape == (1338, 7)
    assert 'sexe' in result.columns
    assert 'imc' in result.columns
