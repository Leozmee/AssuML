"""Tests unitaires pour business/scoring.py et business/risk_engine.py."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from business.scoring import calculer_prime  # noqa: E402
from business.risk_engine import get_categorie_risque, get_decision  # noqa: E402


# ── Tests calculer_prime ────────────────────────────────────────────────────


def test_calculer_prime_faible():
    """Prime catégorie faible = coût × 1.20."""
    assert calculer_prime(10_000.0, "faible") == pytest.approx(12_000.0)


def test_calculer_prime_moyen():
    """Prime catégorie moyen = coût × 1.35."""
    assert calculer_prime(10_000.0, "moyen") == pytest.approx(13_500.0)


def test_calculer_prime_eleve():
    """Prime catégorie eleve = coût × 1.50."""
    assert calculer_prime(10_000.0, "eleve") == pytest.approx(15_000.0)


def test_calculer_prime_critique():
    """Prime catégorie critique = coût × 1.80."""
    assert calculer_prime(10_000.0, "critique") == pytest.approx(18_000.0)


def test_calculer_prime_invalid_category():
    """calculer_prime() doit lever KeyError pour une catégorie inconnue."""
    with pytest.raises(KeyError):
        calculer_prime(10_000.0, "inconnu")


# ── Tests get_decision ──────────────────────────────────────────────────────


def test_get_decision_mapping():
    """get_decision() doit retourner les bonnes décisions pour les 4 catégories."""
    assert get_decision("faible") == "accepter"
    assert get_decision("moyen") == "accepter"
    assert get_decision("eleve") == "examiner"
    assert get_decision("critique") == "refuser"


def test_get_decision_invalid():
    """get_decision() doit lever ValueError pour une catégorie inconnue."""
    with pytest.raises(ValueError):
        get_decision("inconnu")


# ── Tests get_categorie_risque ──────────────────────────────────────────────


def test_get_categorie_risque_faible_sous_seuil():
    """< 5 000 USD → faible."""
    assert get_categorie_risque(4_999.99) == "faible"


def test_get_categorie_risque_moyen_debut():
    """5 000 USD → moyen (seuil inclus)."""
    assert get_categorie_risque(5_000.0) == "moyen"


def test_get_categorie_risque_moyen_fin():
    """14 999 USD → moyen."""
    assert get_categorie_risque(14_999.99) == "moyen"


def test_get_categorie_risque_eleve_debut():
    """15 000 USD → eleve (seuil inclus)."""
    assert get_categorie_risque(15_000.0) == "eleve"


def test_get_categorie_risque_eleve_fin():
    """29 999 USD → eleve."""
    assert get_categorie_risque(29_999.99) == "eleve"


def test_get_categorie_risque_critique():
    """≥ 30 000 USD → critique."""
    assert get_categorie_risque(30_000.0) == "critique"
    assert get_categorie_risque(50_000.0) == "critique"
