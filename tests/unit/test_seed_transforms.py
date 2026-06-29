"""Tests unitaires pour les fonctions de transformation de database/seed.py."""

import pytest

from database.seed import REGIONS, transformer_ligne


# ── Fixtures ──────────────────────────────────────────────────────────────────

REGIONS_MAP = {"southwest": 1, "southeast": 2, "northwest": 3, "northeast": 4}

ROW_BASE = {
    "age": "45",
    "sex": "male",
    "bmi": "32.00",
    "children": "2",
    "smoker": "no",
    "region": "southeast",
    "charges": "12345.67",
}


# ── Tests mapping sexe ────────────────────────────────────────────────────────


def test_mapping_sexe_male():
    """male doit être converti en homme."""
    row = {**ROW_BASE, "sex": "male"}
    result = transformer_ligne(row, REGIONS_MAP)
    assert result["sexe"] == "homme"


def test_mapping_sexe_female():
    """female doit être converti en femme."""
    row = {**ROW_BASE, "sex": "female"}
    result = transformer_ligne(row, REGIONS_MAP)
    assert result["sexe"] == "femme"


# ── Tests mapping fumeur ──────────────────────────────────────────────────────


def test_mapping_fumeur_yes():
    """smoker=yes doit être converti en True."""
    row = {**ROW_BASE, "smoker": "yes"}
    result = transformer_ligne(row, REGIONS_MAP)
    assert result["fumeur"] is True


def test_mapping_fumeur_no():
    """smoker=no doit être converti en False."""
    row = {**ROW_BASE, "smoker": "no"}
    result = transformer_ligne(row, REGIONS_MAP)
    assert result["fumeur"] is False


# ── Tests régions ─────────────────────────────────────────────────────────────


def test_regions_definies():
    """Les 4 régions attendues doivent être présentes dans REGIONS."""
    assert set(REGIONS) == {"southwest", "southeast", "northwest", "northeast"}


def test_region_lookup_valide():
    """La région southwest doit retourner region_id=1."""
    row = {**ROW_BASE, "region": "southwest"}
    result = transformer_ligne(row, REGIONS_MAP)
    assert result["region_id"] == 1


def test_region_inconnue_leve_erreur():
    """Une région inconnue doit lever une ValueError."""
    row = {**ROW_BASE, "region": "unknown"}
    with pytest.raises(ValueError, match="Région inconnue"):
        transformer_ligne(row, REGIONS_MAP)


# ── Tests imc et types ────────────────────────────────────────────────────────


def test_imc_arrondi():
    """bmi=27.9 doit être arrondi à 2 décimales."""
    row = {**ROW_BASE, "bmi": "27.900"}
    result = transformer_ligne(row, REGIONS_MAP)
    assert result["imc"] == 27.9
    assert isinstance(result["imc"], float)


def test_age_est_entier():
    """age doit être un entier."""
    result = transformer_ligne(ROW_BASE, REGIONS_MAP)
    assert isinstance(result["age"], int)
    assert result["age"] == 45


def test_enfants_est_entier():
    """children doit être converti en entier."""
    row = {**ROW_BASE, "children": "3"}
    result = transformer_ligne(row, REGIONS_MAP)
    assert isinstance(result["enfants"], int)
    assert result["enfants"] == 3


def test_email_telephone_null():
    """email et telephone doivent être None (RGPD — non présents dans le CSV)."""
    result = transformer_ligne(ROW_BASE, REGIONS_MAP)
    assert result["email"] is None
    assert result["telephone"] is None


def test_charges_ignorees():
    """charges du CSV ne doit pas apparaître dans le résultat."""
    result = transformer_ligne(ROW_BASE, REGIONS_MAP)
    assert "charges" not in result


def test_sexe_invalide_leve_erreur():
    """Une valeur de sexe inconnue doit lever une ValueError."""
    row = {**ROW_BASE, "sex": "unknown"}
    with pytest.raises(ValueError, match="Sexe inconnu"):
        transformer_ligne(row, REGIONS_MAP)


def test_fumeur_invalide_leve_erreur():
    """Une valeur de fumeur inconnue doit lever une ValueError."""
    row = {**ROW_BASE, "smoker": "maybe"}
    with pytest.raises(ValueError, match="Valeur fumeur inconnue"):
        transformer_ligne(row, REGIONS_MAP)
