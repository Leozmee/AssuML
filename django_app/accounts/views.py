"""Vues d'authentification et de profil utilisateur AssuML."""

import csv
import io
import json
import zipfile

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import superuser_required
from accounts.forms import (
    CreateAdminForm,
    LoginForm,
    MonCompteEditForm,
    RegisterStep1Form,
    RegisterStep2Form,
)
from accounts.models import ProfilUtilisateur, User
from utils import (
    api_client,
    client_to_predict_payload,
    region_id_to_nom,
    region_nom_to_id,
)
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


def register_step1_view(request):
    """Inscription assuré — étape 1/2 : email + mot de passe (stockés en session)."""
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    form = RegisterStep1Form(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        # Rien n'est créé en base à cette étape — on garde juste les identifiants
        # validés en session le temps que l'étape 2 soit complétée.
        request.session["register_email"] = cd["email"]
        request.session["register_password"] = cd["password1"]
        request.session["register_telephone"] = cd.get("telephone") or ""
        return redirect("accounts:register_step2")

    return render(request, "accounts/register_step1.html", {"form": form})


def register_step2_view(request):
    """Inscription assuré — étape 2/2 : profil médical, puis création atomique."""
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    email = request.session.get("register_email")
    password = request.session.get("register_password")
    telephone = request.session.get("register_telephone") or None
    if not email or not password:
        messages.warning(request, "Merci de renseigner d'abord vos identifiants.")
        return redirect("accounts:register")

    form = RegisterStep2Form(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data

        # Étape 1 — créer le User Django
        user = User.objects.create_user(email=email, password=password)

        # Étape 2 — créer le client dans PostgreSQL via FastAPI
        try:
            client = api_client.create_client(
                {
                    "nom": cd["nom"],
                    "prenom": cd["prenom"],
                    "age": cd["age"],
                    "sexe": cd["sexe"],
                    "imc": round(cd["imc"], 2),
                    "enfants": cd["enfants"],
                    "fumeur": cd["fumeur"],
                    "region_id": region_nom_to_id(cd["region"]),
                    "email": email,
                    "telephone": telephone,
                    "a_un_compte": True,
                }
            )
            client_id = client["client_id"]
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            # Rollback étape 1
            user.delete()
            messages.error(request, f"Erreur lors de la création du compte : {exc}")
            return render(request, "accounts/register_step2.html", {"form": form})

        # Étape 3 — créer le ProfilUtilisateur
        ProfilUtilisateur.objects.create(user=user, role="user", client_id=client_id)

        del request.session["register_email"]
        del request.session["register_password"]
        request.session.pop("register_telephone", None)

        login(request, user)
        messages.success(request, "Compte créé avec succès. Bienvenue !")
        return redirect("accounts:mon_compte")

    return render(request, "accounts/register_step2.html", {"form": form})


@superuser_required
def create_admin_view(request):
    """Création d'un compte admin (réservé au super-admin)."""
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
            return redirect("accounts:create_admin")

    admins = (
        User.objects.filter(profil__role="admin")
        .select_related("profil")
        .order_by("email")
    )
    return render(
        request, "accounts/create_admin.html", {"form": form, "admins": admins}
    )


@superuser_required
def delete_admin_view(request, user_id):
    """Suppression d'un compte admin (réservé au super-admin)."""
    admin_user = get_object_or_404(User, pk=user_id, profil__role="admin")

    if admin_user == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect("accounts:create_admin")

    if request.method == "POST":
        email = admin_user.email
        admin_user.delete()
        messages.success(request, f"Compte admin {email} supprimé.")
        return redirect("accounts:create_admin")

    return render(request, "accounts/delete_admin.html", {"admin_user": admin_user})


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
            for contrat in contrats:
                contrat["prime_annuelle"] = contrat["prime_mensuelle"] * 12
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
def export_donnees_view(request):
    """Export des données personnelles de l'assuré, en JSON et en CSV.

    Limité aux sections "Mes informations" et "Mon contrat" (pas
    l'historique des évaluations ML, hors périmètre de cet export). Les
    deux formats sont générés en une seule fois et livrés dans une
    archive ZIP unique (un seul bouton, un seul téléchargement) : JSON
    comme format structuré courant (cf. article 20 du RGPD), cohérent
    avec le reste de l'application qui communique déjà en JSON ; CSV en
    complément pour une ouverture directe dans un tableur.
    """
    try:
        profil = request.user.profil
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil introuvable.")
        return redirect("accounts:login")

    if profil.role != "user":
        return redirect("gestion:list")

    try:
        client = api_client.get_client(profil.client_id)
        if client:
            client["region_nom"] = region_id_to_nom(client["region_id"])
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.warning(request, f"Impossible de charger vos informations : {exc}")
        return redirect("accounts:mon_compte")

    try:
        contrats = api_client.get_contrats(client_id=profil.client_id) or []
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        contrats = []

    mes_informations = {
        "age": client.get("age"),
        "sexe": client.get("sexe"),
        "imc": client.get("imc"),
        "enfants": client.get("enfants"),
        "fumeur": client.get("fumeur"),
        "region": client.get("region_nom"),
        "email": client.get("email"),
        "telephone": client.get("telephone"),
    }
    mon_contrat = [
        {
            "type_couverture": c.get("type_couverture"),
            "statut": c.get("statut"),
            "prime_mensuelle": c.get("prime_mensuelle"),
            "prime_annuelle": (
                c["prime_mensuelle"] * 12
                if c.get("prime_mensuelle") is not None
                else None
            ),
            "date_debut": c.get("date_debut"),
        }
        for c in contrats
    ]

    export = {"mes_informations": mes_informations, "mon_contrat": mon_contrat}
    contenu_json = json.dumps(export, ensure_ascii=False, indent=2)

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["Mes informations"])
    writer.writerow(list(mes_informations.keys()))
    writer.writerow(list(mes_informations.values()))
    writer.writerow([])
    writer.writerow(["Mon contrat"])
    writer.writerow(
        ["type_couverture", "statut", "prime_mensuelle", "prime_annuelle", "date_debut"]
    )
    for contrat in mon_contrat:
        writer.writerow(
            [
                contrat["type_couverture"],
                contrat["statut"],
                contrat["prime_mensuelle"],
                contrat["prime_annuelle"],
                contrat["date_debut"],
            ]
        )
    contenu_csv = csv_buffer.getvalue()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as archive:
        archive.writestr("mes_donnees_assuml.json", contenu_json)
        archive.writestr("mes_donnees_assuml.csv", contenu_csv)

    reponse = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    reponse["Content-Disposition"] = 'attachment; filename="mes_donnees_assuml.zip"'
    return reponse


@login_required
def resilier_contrat_view(request, contrat_id):
    """Résiliation d'un contrat par son titulaire (confirmation requise).

    Sécurité : le contrat doit appartenir au client connecté — vérifié en
    le recherchant parmi ses propres contrats plutôt qu'en faisant
    confiance à contrat_id seul (un client ne doit pas pouvoir résilier
    le contrat d'un autre en devinant un identifiant).
    """
    try:
        profil = request.user.profil
    except ProfilUtilisateur.DoesNotExist:
        messages.error(request, "Profil introuvable.")
        return redirect("accounts:login")

    if profil.role != "user":
        return redirect("gestion:list")

    contrat = None
    try:
        contrats = api_client.get_contrats(client_id=profil.client_id) or []
        contrat = next((c for c in contrats if c["contrat_id"] == contrat_id), None)
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    if contrat is None:
        messages.error(request, "Contrat introuvable.")
        return redirect("accounts:mon_compte")

    if request.method == "POST":
        try:
            api_client.update_contrat_statut(contrat_id, "resilie")
            messages.success(request, "Votre contrat a été résilié.")
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur lors de la résiliation : {exc}")
        return redirect("accounts:mon_compte")

    return render(request, "accounts/resilier_contrat.html", {"contrat": contrat})


@login_required
def simulation_view(request):
    """Simulation de scoring par l'assuré sur son propre profil.

    Utilise /predict/complet sans client_id : le calcul est fait par les
    mêmes modèles ML que le scoring admin, mais rien n'est persisté en base
    (la persistance dans `predictions` n'a lieu que si client_id est fourni).
    Seul le montant final (prime, coût déjà incluse) est restitué —
    jamais le coût brut, le score ou la catégorie de risque.
    """
    try:
        profil = request.user.profil
    except ProfilUtilisateur.DoesNotExist:
        return redirect("accounts:login")

    if profil.role != "user":
        return redirect("gestion:list")

    client = None
    montant = None

    try:
        client = api_client.get_client(profil.client_id)
        if client:
            client["region_nom"] = region_id_to_nom(client["region_id"])
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.warning(request, f"Impossible de charger vos informations : {exc}")

    if request.method == "POST" and client:
        try:
            resultat = api_client.predict_complet(client_to_predict_payload(client))
            montant = {
                "annuel": round(resultat["prime"], 2),
                "mensuel": round(resultat["prime"] / 12, 2),
            }
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur lors de la simulation : {exc}")

    return render(
        request,
        "accounts/simulation.html",
        {"client": client, "montant": montant},
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
