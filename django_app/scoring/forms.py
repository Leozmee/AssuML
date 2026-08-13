"""Formulaire de scoring ML."""

from django import forms
from utils.forms import AccessibleFormMixin
from django.core.exceptions import ValidationError

REGIONS = [
    ("", "— Sélectionner —"),
    ("southwest", "Sud-Ouest (Southwest)"),
    ("southeast", "Sud-Est (Southeast)"),
    ("northwest", "Nord-Ouest (Northwest)"),
    ("northeast", "Nord-Est (Northeast)"),
]

SEXES = [
    ("", "— Sélectionner —"),
    ("homme", "Homme"),
    ("femme", "Femme"),
]


class ScoringForm(AccessibleFormMixin, forms.Form):
    """Données assuré → scoring complet (coût + risque + prime + décision)."""

    age = forms.IntegerField(
        min_value=18,
        max_value=64,
        label="Âge",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    sexe = forms.ChoiceField(
        choices=SEXES,
        label="Sexe",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    poids = forms.DecimalField(
        min_value=30,
        max_value=300,
        decimal_places=1,
        label="Poids (kg)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
    )
    taille = forms.IntegerField(
        min_value=100,
        max_value=250,
        label="Taille (cm)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    enfants = forms.IntegerField(
        min_value=0,
        max_value=5,
        label="Nombre d'enfants",
        initial=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    fumeur = forms.BooleanField(
        required=False,
        label="Fumeur",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    region = forms.ChoiceField(
        choices=REGIONS,
        label="Région",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        cleaned = super().clean()
        poids = cleaned.get("poids")
        taille = cleaned.get("taille")
        if poids and taille and taille > 0:
            cleaned["imc"] = float(poids) / (float(taille) / 100) ** 2
        else:
            raise ValidationError("Poids et taille sont obligatoires.")
        return cleaned
