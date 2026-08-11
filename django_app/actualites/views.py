"""Vue actualités — articles (admin uniquement)."""

from django.contrib import messages
from django.shortcuts import render

from accounts.decorators import admin_required
from utils.api_client import (
    ApiError,
    ApiTimeoutError,
    ApiUnavailableError,
    get_articles,
)

SOURCES = [("", "Toutes sources"), ("santemagazine.fr", "Santé Magazine")]


@admin_required
def actualites_list(request):
    """Articles filtrés par source."""
    source = request.GET.get("source", "")

    articles = []

    try:
        articles = (get_articles(source=source or None) or {}).get("items", [])
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.warning(request, f"Articles indisponibles : {exc}")

    return render(
        request,
        "actualites/list.html",
        {
            "articles": articles,
            "sources": SOURCES,
            "source_sel": source,
        },
    )
