"""Vues CRUD clients et contrats — admin uniquement."""

from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.decorators import admin_required
from gestion.forms import ClientForm, ContratForm
from utils import api_client, region_id_to_nom, region_nom_to_id
from utils.api_client import ApiError, ApiTimeoutError, ApiUnavailableError

COEFFICIENTS = {"faible": 1.20, "moyen": 1.35, "eleve": 1.50, "critique": 1.80}


def _enrichir(res: dict) -> dict:
    """Ajoute les champs dérivés au résultat de predict_complet."""
    res["cout_mensuel"] = round(res["cout_predit"] / 12, 2)
    res["prime_annuelle"] = res["prime"]
    res["prime_mensuelle"] = round(res["prime"] / 12, 2)
    res["marge_annuelle"] = round(res["prime"] - res["cout_predit"], 2)
    res["coefficient_marge"] = COEFFICIENTS.get(res["categorie_risque"], "—")
    return res


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
        risque_map = {p["client_id"]: p["categorie_risque"] for p in dernieres}
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    for client in clients:
        client["contrat"] = contrats_map.get(client["client_id"])
        client["categorie_risque"] = risque_map.get(client["client_id"])
        client["region_nom"] = region_id_to_nom(client["region_id"])

    # Recherche par ID
    q = request.GET.get("q", "").strip()
    if q.isdigit():
        clients = [c for c in clients if str(c["client_id"]) == q]

    # Tri
    RISQUE_ORDRE = {"faible": 1, "moyen": 2, "eleve": 3, "critique": 4}
    sort = request.GET.get("sort", "id_asc")
    if sort == "id_asc":
        clients.sort(key=lambda c: c["client_id"])
    elif sort == "id_desc":
        clients.sort(key=lambda c: c["client_id"], reverse=True)
    elif sort == "risque_asc":
        clients.sort(key=lambda c: RISQUE_ORDRE.get(c["categorie_risque"], 0))
    elif sort == "risque_desc":
        clients.sort(
            key=lambda c: RISQUE_ORDRE.get(c["categorie_risque"], 0), reverse=True
        )

    return render(
        request, "gestion/list.html", {"clients": clients, "q": q, "sort": sort}
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

    return render(
        request,
        "gestion/detail.html",
        {"client": client, "contrats": contrats, "predictions": predictions},
    )


@admin_required
def client_create(request):
    """Créer un nouveau client (admin)."""
    form = ClientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        try:
            api_client.create_client(
                {
                    "age": cd["age"],
                    "sexe": cd["sexe"],
                    "imc": round(cd["imc"], 2),
                    "enfants": cd["enfants"],
                    "fumeur": cd["fumeur"],
                    "region_id": region_nom_to_id(cd["region"]),
                    "email": cd.get("email") or None,
                    "a_un_compte": False,
                }
            )
            messages.success(request, "Client créé avec succès.")
            return redirect("gestion:list")
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur lors de la création : {exc}")

    return render(request, "gestion/create.html", {"form": form})


@admin_required
def client_update(request, client_id):
    """Modifier un client existant."""
    try:
        client = api_client.get_client(client_id)
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.error(request, f"Client introuvable : {exc}")
        return redirect("gestion:list")

    initial = {
        "age": client["age"],
        "sexe": client["sexe"],
        "enfants": client["enfants"],
        "fumeur": client["fumeur"],
        "region": region_id_to_nom(client["region_id"]),
        "email": client.get("email") or "",
        "imc_courant": client["imc"],
    }
    form = ClientForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        try:
            api_client.update_client(
                client_id,
                {
                    "age": cd["age"],
                    "sexe": cd["sexe"],
                    "imc": round(cd["imc"], 2),
                    "enfants": cd["enfants"],
                    "fumeur": cd["fumeur"],
                    "region_id": region_nom_to_id(cd["region"]),
                    "email": cd.get("email") or None,
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
            raw = api_client.predict_complet(
                {
                    "age": client["age"],
                    "sexe": 0 if client["sexe"] == "homme" else 1,
                    "imc": float(client["imc"]),
                    "enfants": client["enfants"],
                    "fumeur": 1 if client["fumeur"] else 0,
                    "region": region_id_to_nom(client["region_id"]),
                    "client_id": client["client_id"],
                }
            )
            resultat = _enrichir(raw)
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur de scoring : {exc}")

    return render(
        request,
        "gestion/score.html",
        {"client": client, "resultat": resultat},
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
