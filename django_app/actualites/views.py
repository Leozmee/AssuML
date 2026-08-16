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


@login_required(login_url="/accounts/login/")
def actualites_list(request):
    """Articles de santé (source unique : Santé Magazine — pas de filtre)."""
    articles = []

    try:
        articles = (get_articles() or {}).get("items", [])
    except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
        messages.warning(request, f"Articles indisponibles : {exc}")

    return render(request, "actualites/list.html", {"articles": articles})
