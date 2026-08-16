"""Formulaires d'authentification et de profil utilisateur."""

from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from accounts.models import User
from utils import capitaliser_nom
from utils.forms import AccessibleFormMixin

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


class LoginForm(AccessibleFormMixin, forms.Form):
    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )


class PasswordChangeForm(AccessibleFormMixin, DjangoPasswordChangeForm):
    """Modification du mot de passe — utilisateur déjà connecté (admin ou assuré)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("old_password", "new_password1", "new_password2"):
            self.fields[name].widget.attrs["class"] = "form-control"
        self.fields["old_password"].widget.attrs["autofocus"] = True


class RegisterStep1Form(AccessibleFormMixin, UserCreationForm):
    """Inscription assuré — étape 1/2 : identifiants (email + mot de passe)."""

    # telephone n'est pas un champ du modèle User (Meta.fields) — c'est un
    # attribut du Client FastAPI/PostgreSQL, déclaré ici comme champ
    # additionnel du formulaire, au même titre qu'un ModelForm peut porter
    # des champs hors modèle.
    telephone = forms.CharField(
        max_length=20,
        required=False,
        label="Téléphone (optionnel)",
        widget=forms.TextInput(
            attrs={"class": "form-control", "type": "tel", "autocomplete": "off"}
        ),
    )

    class Meta:
        model = User
        fields = ("email", "password1", "password2")
        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "form-control", "autocomplete": "email"}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["class"] = "form-control"


class RegisterStep2Form(AccessibleFormMixin, forms.Form):
    """Inscription assuré — étape 2/2 : profil médical (poids/taille → IMC)."""

    nom = forms.CharField(
        max_length=100,
        label="Nom",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    prenom = forms.CharField(
        max_length=100,
        label="Prénom",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
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
        else:
            raise ValidationError("Poids et taille sont obligatoires.")
        return cleaned


class CreateAdminForm(AccessibleFormMixin, forms.Form):
    """Création d'un compte admin par un admin existant."""

    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned


class MonCompteEditForm(AccessibleFormMixin, forms.Form):
    """Modification des infos personnelles d'un assuré (poids/taille → IMC)."""

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
