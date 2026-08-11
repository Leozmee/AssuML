"""URLs racine AssuML Django."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("scoring/", include("scoring.urls")),
    path("analytics/", include("analytics.urls")),
    path("gestion/", include("gestion.urls")),
    path("monitoring/", include("monitoring.urls")),
    path("actualites/", include("actualites.urls")),
    path("rgpd/", TemplateView.as_view(template_name="legal/rgpd.html"), name="rgpd"),
    path(
        "contact/",
        TemplateView.as_view(template_name="legal/contact.html"),
        name="contact",
    ),
]
