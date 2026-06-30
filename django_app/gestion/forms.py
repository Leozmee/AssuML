"""Formulaires CRUD clients et contrats."""

from django import forms
from django.core.exceptions import ValidationError

REGIONS = [
    ("", "— Sélectionner —"),
    ("southwest", "Sud-Ouest"),
    ("southeast", "Sud-Est"),
    ("northwest", "Nord-Ouest"),
    ("northeast", "Nord-Est"),
]

SEXES = [
    ("", "— Sélectionner —"),
    ("homme", "Homme"),
    ("femme", "Femme"),
]

TYPES_COUVERTURE = [
    ("", "— Sélectionner —"),
    ("basique", "Basique"),
    ("standard", "Standard"),
    ("premium", "Premium"),
    ("famille", "Famille"),
]


class ClientForm(forms.Form):
    """Formulaire création / modification client (admin). IMC calculé depuis poids/taille."""  # noqa: E501

    age = forms.IntegerField(
        min_value=18,
        max_value=120,
        label="Âge",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    sexe = forms.ChoiceField(
        choices=SEXES,
        label="Sexe",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    imc_courant = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(),
    )
    poids = forms.DecimalField(
        min_value=30,
        max_value=300,
        decimal_places=1,
        required=False,
        label="Poids (kg)",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.1",
                "placeholder": "Laisser vide pour garder l'IMC actuel",
            }
        ),
    )
    taille = forms.IntegerField(
        min_value=100,
        max_value=250,
        required=False,
        label="Taille (cm)",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Laisser vide pour garder l'IMC actuel",
            }
        ),
    )
    enfants = forms.IntegerField(
        min_value=0,
        max_value=10,
        label="Enfants à charge",
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
    email = forms.EmailField(
        required=False,
        label="Email (optionnel)",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned = super().clean()
        poids = cleaned.get("poids")
        taille = cleaned.get("taille")
        if poids and taille and taille > 0:
            cleaned["imc"] = float(poids) / (float(taille) / 100) ** 2
        elif cleaned.get("imc_courant"):
            cleaned["imc"] = float(cleaned["imc_courant"])
        else:
            raise ValidationError(
                "Poids et taille sont obligatoires pour calculer l'IMC."
            )
        return cleaned


class ContratForm(forms.Form):
    """Formulaire création contrat (admin)."""

    type_couverture = forms.ChoiceField(
        choices=TYPES_COUVERTURE,
        label="Type de couverture",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    prime_mensuelle = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        label="Prime mensuelle (€)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    date_debut = forms.DateField(
        label="Date de début",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
