"""Vue actualités — accessible à tout utilisateur connecté (admin ou client)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from utils.api_client import (
    ApiError,
    ApiTimeoutError,
    ApiUnavailableError,
    get_articles,
)

SOURCES = [("", "Toutes sources"), ("santemagazine.fr", "Santé Magazine")]


@login_required(login_url="/accounts/login/")
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
