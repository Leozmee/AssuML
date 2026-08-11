"""Tests des formulaires AssuML — calcul IMC."""

import pytest

from scoring.forms import ScoringForm
from gestion.forms import ClientForm
from accounts.forms import RegisterStep1Form, RegisterStep2Form


@pytest.mark.django_db
class TestScoringFormIMC:
    def test_calcul_imc_correct(self):
        form = ScoringForm(
            data={
                "age": 30,
                "sexe": "homme",
                "poids": "80.0",
                "taille": "175",
                "enfants": 0,
                "fumeur": False,
                "region": "southwest",
            }
        )
        assert form.is_valid(), form.errors
        imc = form.cleaned_data["imc"]
        assert abs(imc - 26.12) < 0.1

    def test_imc_hors_plage_taille_invalide(self):
        form = ScoringForm(
            data={
                "age": 30,
                "sexe": "homme",
                "poids": "80.0",
                "taille": "50",
                "enfants": 0,
                "fumeur": False,
                "region": "southwest",
            }
        )
        assert not form.is_valid()
        assert "taille" in form.errors

    def test_champs_requis_manquants(self):
        form = ScoringForm(data={"age": 30})
        assert not form.is_valid()


@pytest.mark.django_db
class TestClientFormIMC:
    def test_calcul_imc_correct(self):
        form = ClientForm(
            data={
                "age": 45,
                "sexe": "femme",
                "poids": "65.0",
                "taille": "165",
                "enfants": 2,
                "fumeur": False,
                "region": "northeast",
                "email": "",
            }
        )
        assert form.is_valid(), form.errors
        imc = form.cleaned_data["imc"]
        # 65 / (1.65)^2 = 23.88
        assert abs(imc - 23.88) < 0.1


@pytest.mark.django_db
class TestRegisterStep1Form:
    def test_identifiants_valides(self):
        form = RegisterStep1Form(
            data={
                "email": "test@test.fr",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
            }
        )
        assert form.is_valid(), form.errors

    def test_mots_de_passe_differents(self):
        form = RegisterStep1Form(
            data={
                "email": "test@test.fr",
                "password1": "TestPass123!",
                "password2": "AutrePass456!",
            }
        )
        assert not form.is_valid()


class TestRegisterStep2FormIMC:
    def test_profil_valide(self):
        form = RegisterStep2Form(
            data={
                "age": 25,
                "sexe": "homme",
                "poids": "70.0",
                "taille": "180",
                "enfants": 0,
                "fumeur": False,
                "region": "northwest",
            }
        )
        assert form.is_valid(), form.errors
        imc = form.cleaned_data["imc"]
        # 70 / (1.80)^2 = 21.60
        assert abs(imc - 21.60) < 0.1
