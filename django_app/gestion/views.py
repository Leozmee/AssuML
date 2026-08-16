"""Vues CRUD clients et contrats — admin uniquement."""

from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.decorators import admin_required
from accounts.models import ProfilUtilisateur, User
from gestion.forms import ClientForm, ContratForm, ContratTypeForm
from utils import (
    api_client,
    client_identite,
    client_to_predict_payload,
    enrichir_resultat_scoring,
    filtrer_trier_clients,
    imc_vers_poids_taille,
    region_id_to_nom,
    region_nom_to_id,
)
from utils.api_client import ApiError, ApiTimeoutError, ApiUnavailableError


def _prime_a_verifier(contrat: dict, client: dict, last_inputs: dict | None) -> bool:
    """Détecte une prime potentiellement obsolète face au profil ML du client.

    Compare uniquement les champs qui influencent le scoring (âge, sexe, IMC,
    enfants, tabagisme, région) à ceux de la dernière prédiction — modifier le
    nom, prénom, email ou téléphone n'a aucun impact sur la prédiction et ne
    doit donc pas déclencher l'alerte. Signalé uniquement pour les contrats
    actifs. `last_inputs` vient du décodage de `version_modele` (API), None si
    le client n'a jamais été scoré.
    """
    if not contrat or contrat.get("statut") != "actif":
        return False
    if not last_inputs:
        return True
    try:
        imc_client = round(float(client.get("imc")), 2)
    except (TypeError, ValueError):
        return True
    sexe_code = 0 if client.get("sexe") == "homme" else 1
    fumeur_code = 1 if client.get("fumeur") else 0
    return (
        client.get("age") != last_inputs.get("age")
        or sexe_code != last_inputs.get("sexe")
        or imc_client != last_inputs.get("imc")
        or client.get("enfants") != last_inputs.get("enfants")
        or fumeur_code != last_inputs.get("fumeur")
        or client.get("region_nom") != last_inputs.get("region")
    )


@admin_required
def client_list(request):
    """Liste tous les clients avec statut contrat."""
    clients = []
    contrats_map = {}

    try:
        clients = api_client.get_all_clients() or []
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.error(request, f"Impossible de charger les clients : {exc}")

    try:
        contrats = api_client.get_all_contrats() or []
        for c in contrats:
            cid = c.get("client_id")
            if cid not in contrats_map:
                contrats_map[cid] = c
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    risque_map = {}
    try:
        dernieres = api_client.get_dernieres_predictions() or []
        risque_map = {p["client_id"]: p for p in dernieres}
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    for client in clients:
        client["contrat"] = contrats_map.get(client["client_id"])
        derniere = risque_map.get(client["client_id"])
        client["categorie_risque"] = (
            derniere.get("categorie_risque") if derniere else None
        )
        client["region_nom"] = region_id_to_nom(client["region_id"])
        client["identite"] = client_identite(client)
        client["prime_a_verifier"] = _prime_a_verifier(
            client["contrat"], client, derniere.get("inputs") if derniere else None
        )

    # Recherche par ID/nom/prénom : filtrage instantané côté client (JS), pas ici.

    compte = request.GET.get("compte", "")
    contrat_filtre = request.GET.get("contrat", "")
    sort = request.GET.get("sort", "id_asc")
    clients = filtrer_trier_clients(clients, sort, compte, contrat_filtre)

    return render(
        request,
        "gestion/list.html",
        {
            "clients": clients,
            "sort": sort,
            "compte": compte,
            "contrat_filtre": contrat_filtre,
        },
    )


@admin_required
def client_detail(request, client_id):
    """Fiche détail d'un client."""
    client = None
    contrats = []
    predictions = []

    try:
        client = api_client.get_client(client_id)
        client["region_nom"] = region_id_to_nom(client["region_id"])
        client["identite"] = client_identite(client)
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.error(request, f"Client introuvable : {exc}")
        return redirect("gestion:list")

    try:
        contrats = api_client.get_contrats(client_id=client_id) or []
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    try:
        predictions = api_client.get_predictions_client(client_id) or []
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    prime_a_verifier = _prime_a_verifier(
        contrats[0] if contrats else None,
        client,
        predictions[0].get("inputs") if predictions else None,
    )

    return render(
        request,
        "gestion/detail.html",
        {
            "client": client,
            "contrats": contrats,
            "predictions": predictions,
            "prime_a_verifier": prime_a_verifier,
        },
    )


@admin_required
def client_create(request):
    """Créer un nouveau client (admin)."""
    form = ClientForm(request.POST or None, require_identite=True)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        creer_compte = cd.get("creer_compte")

        user = None
        if creer_compte:
            # Créé en premier — facile à annuler (rollback) si l'API échoue.
            user = User.objects.create_user(email=cd["email"], password=cd["password1"])

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
                    "email": cd.get("email") or None,
                    "telephone": cd.get("telephone") or None,
                    "a_un_compte": bool(creer_compte),
                }
            )
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            if user is not None:
                user.delete()
            messages.error(request, f"Erreur lors de la création : {exc}")
            return render(request, "gestion/create.html", {"form": form})

        if creer_compte:
            ProfilUtilisateur.objects.create(
                user=user, role="user", client_id=client["client_id"]
            )
            messages.success(request, "Client et compte créés avec succès.")
        else:
            messages.success(request, "Client créé avec succès.")

        return redirect("gestion:list")

    return render(request, "gestion/create.html", {"form": form})


@admin_required
def client_update(request, client_id):
    """Modifier un client existant."""
    try:
        client = api_client.get_client(client_id)
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.error(request, f"Client introuvable : {exc}")
        return redirect("gestion:list")

    taille_reconstruite, poids_reconstruit = imc_vers_poids_taille(client["imc"])
    initial = {
        "nom": client.get("nom") or "",
        "prenom": client.get("prenom") or "",
        "age": client["age"],
        "sexe": client["sexe"],
        "enfants": client["enfants"],
        "fumeur": client["fumeur"],
        "region": region_id_to_nom(client["region_id"]),
        "email": client.get("email") or "",
        "telephone": client.get("telephone") or "",
        "imc_courant": client["imc"],
        # Ni l'un ni l'autre n'est la vraie taille/poids du client (jamais
        # stockés en base) — reconstruits pour préremplir le formulaire avec
        # des valeurs cohérentes avec l'IMC actuel, éditables si besoin.
        "taille": taille_reconstruite,
        "poids": poids_reconstruit,
    }
    form = ClientForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        try:
            api_client.update_client(
                client_id,
                {
                    "nom": cd.get("nom") or None,
                    "prenom": cd.get("prenom") or None,
                    "age": cd["age"],
                    "sexe": cd["sexe"],
                    "imc": round(cd["imc"], 2),
                    "enfants": cd["enfants"],
                    "fumeur": cd["fumeur"],
                    "region_id": region_nom_to_id(cd["region"]),
                    "email": cd.get("email") or None,
                    "telephone": cd.get("telephone") or None,
                },
            )
            messages.success(request, "Client mis à jour.")
            return redirect("gestion:detail", client_id=client_id)
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur lors de la mise à jour : {exc}")

    return render(
        request,
        "gestion/edit.html",
        {"form": form, "client_id": client_id, "imc_actuel": client["imc"]},
    )


@admin_required
def client_delete(request, client_id):
    """Suppression douce d'un client (confirmation requise)."""
    if request.method == "POST":
        try:
            api_client.delete_client(client_id)
            messages.success(request, f"Client #{client_id} supprimé.")
            return redirect("gestion:list")
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur lors de la suppression : {exc}")
            return redirect("gestion:detail", client_id=client_id)

    return render(request, "gestion/delete.html", {"client_id": client_id})


@admin_required
def client_score(request, client_id):
    """Scorer un client existant via les modèles ML."""
    client = None
    resultat = None

    try:
        client = api_client.get_client(client_id)
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.error(request, f"Client introuvable : {exc}")
        return redirect("gestion:list")

    if request.method == "POST":
        try:
            payload = client_to_predict_payload(client)
            payload["client_id"] = client["client_id"]
            raw = api_client.predict_complet(payload)
            resultat = enrichir_resultat_scoring(raw)
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur de scoring : {exc}")

    contrats = []
    try:
        contrats = api_client.get_contrats(client_id=client_id) or []
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    return render(
        request,
        "gestion/score.html",
        {"client": client, "resultat": resultat, "contrats": contrats},
    )


@admin_required
def contrat_create(request, client_id):
    """Créer un contrat pour un client (uniquement si pas de contrat existant)."""
    client = None
    try:
        client = api_client.get_client(client_id)
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.error(request, f"Client introuvable : {exc}")
        return redirect("gestion:list")

    contrats = []
    try:
        contrats = api_client.get_contrats(client_id=client_id) or []
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    if contrats:
        messages.warning(request, "Ce client a déjà un contrat.")
        return redirect("gestion:detail", client_id=client_id)

    # Pré-remplir la prime depuis la dernière prédiction ML
    prime_initiale = None
    try:
        predictions = api_client.get_predictions_client(client_id) or []
        if predictions:
            prime_initiale = predictions[0].get("prime")
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    initial = (
        {"prime_mensuelle": round(prime_initiale / 12, 2)} if prime_initiale else {}
    )
    form = ContratForm(request.POST or None, initial=initial)

    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        try:
            api_client.create_contrat(
                {
                    "client_id": client_id,
                    "type_couverture": cd["type_couverture"],
                    "prime_mensuelle": float(cd["prime_mensuelle"]),
                    "date_debut": str(cd["date_debut"]),
                }
            )
            messages.success(request, "Contrat créé avec succès.")
            return redirect("gestion:detail", client_id=client_id)
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur lors de la création du contrat : {exc}")

    return render(
        request,
        "gestion/contrat_form.html",
        {"form": form, "client": client, "prime_initiale": prime_initiale},
    )


@admin_required
def contrat_update_type(request, client_id, contrat_id):
    """Modifier le type de couverture d'un contrat existant."""
    client = None
    try:
        client = api_client.get_client(client_id)
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.error(request, f"Client introuvable : {exc}")
        return redirect("gestion:list")

    contrat = None
    try:
        contrats = api_client.get_contrats(client_id=client_id) or []
        contrat = next((c for c in contrats if c["contrat_id"] == contrat_id), None)
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    if contrat is None:
        messages.error(request, "Contrat introuvable.")
        return redirect("gestion:detail", client_id=client_id)

    form = ContratTypeForm(
        request.POST or None,
        initial={"type_couverture": contrat["type_couverture"]},
    )

    if request.method == "POST" and form.is_valid():
        try:
            api_client.update_contrat_type(
                contrat_id, form.cleaned_data["type_couverture"]
            )
            messages.success(request, "Type de contrat mis à jour.")
            return redirect("gestion:detail", client_id=client_id)
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur : {exc}")

    return render(
        request,
        "gestion/contrat_edit.html",
        {"form": form, "client": client, "contrat": contrat},
    )


@admin_required
def contrat_update_prime(request, contrat_id):
    """Met à jour la prime du contrat depuis la dernière prédiction ML."""
    if request.method != "POST":
        return redirect("gestion:list")
    client_id = int(request.POST.get("client_id", 0))
    try:
        predictions = api_client.get_predictions_client(client_id) or []
        if not predictions:
            messages.warning(request, "Aucune prédiction disponible pour ce client.")
            return redirect("gestion:detail", client_id=client_id)
        prime_annuelle = predictions[0]["prime"]
        prime_mensuelle = round(prime_annuelle / 12, 2)
        api_client.update_contrat_prime(contrat_id, prime_mensuelle)
        messages.success(
            request,
            f"Prime mise à jour : {prime_mensuelle} €/mois (dernière prédiction ML).",
        )
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.error(request, f"Erreur : {exc}")
    return redirect("gestion:detail", client_id=client_id)


@admin_required
def contrat_update_statut(request, contrat_id):
    """Résilier ou réactiver un contrat (POST uniquement)."""
    if request.method != "POST":
        return redirect("gestion:list")
    nouveau_statut = request.POST.get("statut")
    client_id = request.POST.get("client_id")
    try:
        api_client.update_contrat_statut(contrat_id, nouveau_statut)
        label = "résilié" if nouveau_statut == "resilie" else "réactivé"
        messages.success(request, f"Contrat #{contrat_id} {label}.")
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.error(request, f"Erreur : {exc}")
    if client_id:
        return redirect("gestion:detail", client_id=int(client_id))
    return redirect("gestion:list")
