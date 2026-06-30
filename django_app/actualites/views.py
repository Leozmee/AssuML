"""Vue actualités — articles + météo (admin uniquement)."""

from django.contrib import messages
from django.shortcuts import render

from accounts.decorators import admin_required
from utils.api_client import (
    ApiError,
    ApiTimeoutError,
    ApiUnavailableError,
    get_articles,
    get_meteo,
)

SOURCES = [("", "Toutes sources"), ("api", "API JSON"), ("web", "Web scraping")]
REGIONS = [
    ("", "Toutes régions"),
    ("southwest", "Sud-Ouest"),
    ("southeast", "Sud-Est"),
    ("northwest", "Nord-Ouest"),
    ("northeast", "Nord-Est"),
]
SAISONS = [
    ("", "Toutes saisons"),
    ("hiver", "Hiver"),
    ("printemps", "Printemps"),
    ("ete", "Été"),
    ("automne", "Automne"),
]


@admin_required
def actualites_list(request):
    """Articles filtrés par source + données météo."""
    source = request.GET.get("source", "")
    region = request.GET.get("region", "")
    saison = request.GET.get("saison", "")

    articles = []
    meteo = []

    try:
        articles = get_articles(source=source or None) or []
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.warning(request, f"Articles indisponibles : {exc}")

    try:
        meteo = get_meteo(region=region or None, saison=saison or None) or []
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.warning(request, f"Données météo indisponibles : {exc}")

    return render(
        request,
        "actualites/list.html",
        {
            "articles": articles,
            "meteo": meteo,
            "sources": SOURCES,
            "regions": REGIONS,
            "saisons": SAISONS,
            "source_sel": source,
            "region_sel": region,
            "saison_sel": saison,
        },
    )
