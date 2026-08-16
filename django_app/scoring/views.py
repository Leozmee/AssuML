"""Vue de scoring ML — admin uniquement."""

from django.contrib import messages
from django.shortcuts import render

from accounts.decorators import admin_required
from scoring.forms import ScoringForm
from utils import (
    api_client,
    client_identite,
    enrichir_resultat_scoring,
    filtrer_trier_clients,
    region_id_to_nom,
)
from utils.api_client import (
    ApiError,
    ApiTimeoutError,
    ApiUnavailableError,
    predict_complet,
)


@admin_required
def scoring_view(request):
    """Formulaire de scoring libre, ou à partir d'un client existant sélectionné.

    Si un client_id valide est soumis avec le formulaire, la simulation est
    persistée dans son historique de prédictions (comme le scoring depuis
    la fiche client) — sinon elle reste un calcul libre, non enregistré.
    """
    form = ScoringForm(request.POST or None)
    resultat = None

    clients = []
    try:
        clients = api_client.get_all_clients() or []
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.warning(request, f"Impossible de charger la liste des clients : {exc}")

    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        payload = {
            "age": cd["age"],
            "sexe": 0 if cd["sexe"] == "homme" else 1,
            "imc": round(cd["imc"], 2),
            "enfants": cd["enfants"],
            "fumeur": 1 if cd["fumeur"] else 0,
            "region": cd["region"],
        }

        client_id = request.POST.get("client_id")
        if client_id and any(str(c["client_id"]) == client_id for c in clients):
            payload["client_id"] = int(client_id)

            # Tant que poids/taille n'ont pas été retouchés depuis la sélection
            # du client, on utilise son IMC exact plutôt que celui recalculé à
            # partir de poids/taille (arrondis à 0.1 kg) — un écart de 0.01 sur
            # l'IMC peut suffire à faire basculer une séparation d'arbre dans le
            # classifieur de risque, alors qu'il ne s'agit pas d'une vraie
            # différence de profil.
            imc_exact = request.POST.get("client_imc_exact")
            if imc_exact:
                try:
                    payload["imc"] = round(float(imc_exact), 2)
                except ValueError:
                    pass

        try:
            raw = predict_complet(payload)
            resultat = enrichir_resultat_scoring(raw)
            resultat["client_id"] = payload.get("client_id")
            # Réémis dans le hidden field côté template : une resoumission du
            # formulaire sans repasser par "Sélectionner" doit rester exacte,
            # pas retomber sur l'IMC reconstruit à partir de poids/taille.
            if payload.get("client_id"):
                resultat["client_imc_exact"] = payload["imc"]
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur de scoring : {exc}")

    contrats_map = {}
    try:
        for c in api_client.get_all_contrats() or []:
            contrats_map.setdefault(c.get("client_id"), c)
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

    if resultat and resultat.get("client_id"):
        client_selectionne = next(
            (c for c in clients if c["client_id"] == resultat["client_id"]), None
        )
        if client_selectionne:
            # "client N" (identité de repli sans nom/prénom) contient déjà le
            # mot "client" — éviter "du client client N" en ne le préfixant
            # que si l'identité réelle (nom/prénom) ne l'a pas déjà.
            identite = client_selectionne["identite"]
            sujet = identite if identite.startswith("client ") else f"client {identite}"
            resultat["client_banner"] = f"Simulation basée sur le profil du {sujet}"

    contrat_filtre = request.GET.get("contrat", "")
    sort = request.GET.get("sort", "id_asc")
    clients = filtrer_trier_clients(clients, sort, "", contrat_filtre)

    return render(
        request,
        "scoring/score.html",
        {
            "form": form,
            "resultat": resultat,
            "clients": clients,
            "sort": sort,
            "contrat_filtre": contrat_filtre,
        },
    )
