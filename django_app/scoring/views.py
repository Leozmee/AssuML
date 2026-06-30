"""Vue de scoring ML — admin uniquement."""

from django.contrib import messages
from django.shortcuts import render

from accounts.decorators import admin_required
from scoring.forms import ScoringForm
from utils.api_client import (
    ApiError,
    ApiTimeoutError,
    ApiUnavailableError,
    predict_complet,
)

# Coefficients de marge par catégorie (cohérents avec business/scoring.py)
COEFFICIENTS = {"faible": 1.20, "moyen": 1.35, "eleve": 1.50, "critique": 1.80}


def _enrichir(res: dict) -> dict:
    """Ajoute les champs dérivés (mensuel, marge, coefficient) au résultat API."""
    res["cout_mensuel"] = round(res["cout_predit"] / 12, 2)
    res["prime_annuelle"] = res["prime"]
    res["prime_mensuelle"] = round(res["prime"] / 12, 2)
    res["marge_annuelle"] = round(res["prime"] - res["cout_predit"], 2)
    res["coefficient_marge"] = COEFFICIENTS.get(res["categorie_risque"], "—")
    return res


@admin_required
def scoring_view(request):
    """Formulaire de scoring libre (sans client existant)."""
    form = ScoringForm(request.POST or None)
    resultat = None

    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        try:
            raw = predict_complet(
                {
                    "age": cd["age"],
                    "sexe": 0 if cd["sexe"] == "homme" else 1,
                    "imc": round(cd["imc"], 2),
                    "enfants": cd["enfants"],
                    "fumeur": 1 if cd["fumeur"] else 0,
                    "region": cd["region"],
                }
            )
            resultat = _enrichir(raw)
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            messages.error(request, f"Erreur de scoring : {exc}")

    return render(request, "scoring/score.html", {"form": form, "resultat": resultat})
