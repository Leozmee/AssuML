"""Vues d'authentification et de profil utilisateur AssuML."""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.decorators import admin_required
from accounts.forms import (
    CreateAdminForm,
    LoginForm,
    MonCompteEditForm,
    RegisterForm,
)
from accounts.models import ProfilUtilisateur, User
from utils import api_client, region_id_to_nom, region_nom_to_id
from utils.api_client import ApiError, ApiTimeoutError, ApiUnavailableError


def login_view(request):
    """Connexion — redirige admin→/gestion/ et user→/mon-compte/."""
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            return _redirect_by_role(user)
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


def register_view(request):
    """Inscription assuré — création atomique User + client PostgreSQL + Profil."""
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data

        # Étape 1 — créer le User Django
        user = User.objects.create_user(
            email=cd["email"],
            password=cd["password1"],
        )

        # Étape 2 — créer le client dans PostgreSQL via FastAPI
        try:
            client = api_client.create_client(
                {
                    "age": cd["age"],
                    "sexe": cd["sexe"],
                    "imc": round(cd["imc"], 2),
                    "enfants": cd["enfants"],
                    "fumeur": cd["fumeur"],
                    "region_id": region_nom_to_id(cd["region"]),
                    "a_un_compte": True,
                }
            )
            client_id = client["client_id"]
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            # Rollback étape 1
            user.delete()
            messages.error(request, f"Erreur lors de la création du compte : {exc}")
            return render(request, "accounts/register.html", {"form": form})

        # Étape 3 — créer le ProfilUtilisateur
        ProfilUtilisateur.objects.create(user=user, role="user", client_id=client_id)

        login(request, user)
        messages.success(request, "Compte créé avec succès. Bienvenue !")
        return redirect("accounts:mon_compte")

    return render(request, "accounts/register.html", {"form": form})


@admin_required
def create_admin_view(request):
    """Création d'un compte admin (réservé aux admins)."""
    form = CreateAdminForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        if User.objects.filter(email=cd["email"]).exists():
            messages.error(request, "Un compte avec cet email existe déjà.")
        else:
            user = User.objects.create_user(
                email=cd["email"],
                password=cd["password"],
            )
            ProfilUtilisateur.objects.create(user=user, role="admin")
            messages.success(request, f"Compte admin créé pour {cd['email']}.")
            return redirect("gestion:list")

    return render(request, "accounts/create_admin.html", {"form": form})


@login_required
def mon_compte_view(request):
    """Page personnelle de l'assuré."""
    try:
        profil = request.user.profil
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil introuvable.")
        return redirect("accounts:login")

    if profil.role != "user":
        return redirect("gestion:list")

    client = None
    contrats = []
    predictions = []

    try:
        client = api_client.get_client(profil.client_id)
        if client:
            client["region_nom"] = region_id_to_nom(client["region_id"])
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.warning(request, f"Impossible de charger vos informations : {exc}")

    if client:
        try:
            contrats = api_client.get_contrats(client_id=profil.client_id) or []
        except (ApiUnavailableError, ApiTimeoutError, ApiError):
            pass
        try:
            predictions = api_client.get_predictions_client(profil.client_id) or []
        except (ApiUnavailableError, ApiTimeoutError, ApiError):
            pass

    return render(
        request,
        "accounts/mon_compte.html",
        {"client": client, "contrats": contrats, "predictions": predictions},
    )


@login_required
def mon_compte_edit_view(request):
    """Modification des infos personnelles de l'assuré."""
    try:
        profil = request.user.profil
    except ProfilUtilisateur.DoesNotExist:
        return redirect("accounts:login")

    if profil.role != "user":
        return redirect("gestion:list")

    form = MonCompteEditForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        try:
            api_client.update_client(
                profil.client_id,
                {
                    "age": cd["age"],
                    "sexe": cd["sexe"],
                    "imc": round(cd["imc"], 2),
                    "enfants": cd["enfants"],
                    "fumeur": cd["fumeur"],
                    "region_id": region_nom_to_id(cd["region"]),
                },
            )
            messages.success(request, "Informations mises à jour.")
            return redirect("accounts:mon_compte")
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur lors de la mise à jour : {exc}")

    return render(request, "accounts/mon_compte_edit.html", {"form": form})


# ── Helpers ────────────────────────────────────────────────────────────────────


def _redirect_by_role(user):
    """Redirige selon le rôle : admin→/gestion/, user→/mon-compte/."""
    try:
        if user.profil.role == "admin":
            return redirect("gestion:list")
    except ProfilUtilisateur.DoesNotExist:
        pass
    return redirect("accounts:mon_compte")
