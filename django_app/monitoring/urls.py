"""URLs de l'application monitoring."""

from django.urls import path

from monitoring import views

app_name = "monitoring"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/refresh/", views.refresh_api, name="refresh"),
]
