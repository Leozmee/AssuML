"""Formulaires CRUD clients et contrats."""

from django import forms
from django.core.exceptions import ValidationError

from accounts.models import User
from utils import capitaliser_nom

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
    """Formulaire création / modification client (admin). IMC calculé depuis poids/taille.

    nom/prenom sont obligatoires uniquement en création (require_identite=True) —
    les clients existants seedés depuis insurance.csv n'en ont pas et doivent
    rester modifiables sans être forcés d'en renseigner un.
    """  # noqa: E501

    nom = forms.CharField(
        max_length=100,
        required=False,
        label="Nom",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    prenom = forms.CharField(
        max_length=100,
        required=False,
        label="Prénom",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
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
    creer_compte = forms.BooleanField(
        required=False,
        label="Créer un compte de connexion pour ce client",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    password1 = forms.CharField(
        required=False,
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        required=False,
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, require_identite=False, **kwargs):
        """require_identite=True force nom/prenom (utilisé à la création)."""
        self.require_identite = require_identite
        super().__init__(*args, **kwargs)

    def clean_nom(self):
        return capitaliser_nom(self.cleaned_data.get("nom", ""))

    def clean_prenom(self):
        return capitaliser_nom(self.cleaned_data.get("prenom", ""))

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

        if self.require_identite:
            if not cleaned.get("nom"):
                raise ValidationError("Le nom est obligatoire.")
            if not cleaned.get("prenom"):
                raise ValidationError("Le prénom est obligatoire.")

        if cleaned.get("creer_compte"):
            email = cleaned.get("email")
            p1 = cleaned.get("password1")
            p2 = cleaned.get("password2")
            if not email:
                raise ValidationError("L'email est obligatoire pour créer un compte.")
            if User.objects.filter(email=email).exists():
                raise ValidationError("Un compte avec cet email existe déjà.")
            if not p1 or not p2:
                raise ValidationError(
                    "Le mot de passe est obligatoire pour créer un compte."
                )
            if p1 != p2:
                raise ValidationError("Les mots de passe ne correspondent pas.")

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
