"""Vues monitoring système — admin uniquement."""

from django.http import JsonResponse
from django.shortcuts import render

from accounts.decorators import admin_required
from utils.api_client import (
    ApiError,
    ApiTimeoutError,
    ApiUnavailableError,
    get_health,
    get_stats_kpis,
)


@admin_required
def dashboard(request):
    """Dashboard de monitoring — santé API + métriques ML."""
    health = None
    kpis = {}

    try:
        health = get_health()
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    try:
        kpis = get_stats_kpis() or {}
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    return render(
        request,
        "monitoring/dashboard.html",
        {"health": health, "kpis": kpis},
    )


@admin_required
def refresh_api(request):
    """Endpoint JSON pour auto-refresh (AJAX toutes les 10s)."""
    data = {}
    try:
        health = get_health()
        if health:
            data["api_status"] = health.get("status", "unknown")
            data["modele_regression"] = health.get("modele_regression", "—")
            data["modele_classification"] = health.get("modele_classification", "—")
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        data["api_status"] = "indisponible"

    try:
        kpis = get_stats_kpis() or {}
        data["total_clients"] = kpis.get("total_clients", "—")
        data["total_predictions"] = kpis.get("total_predictions", "—")
    except (ApiUnavailableError, ApiTimeoutError, ApiError):
        pass

    return JsonResponse(data)
