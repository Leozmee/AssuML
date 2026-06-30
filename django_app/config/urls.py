"""URLs racine AssuML Django."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("scoring/", include("scoring.urls")),
    path("analytics/", include("analytics.urls")),
    path("gestion/", include("gestion.urls")),
    path("monitoring/", include("monitoring.urls")),
    path("actualites/", include("actualites.urls")),
]
