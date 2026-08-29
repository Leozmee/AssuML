"""Vues transverses du projet — page d'accueil."""

from django.shortcuts import render


def home(request):
    """Accueil, visible par tous.

    Un visiteur y trouve la présentation et les accès connexion / inscription ;
    un utilisateur connecté peut y revenir en cliquant sur le logo de la barre
    supérieure. Les appels à l'action s'adaptent à son état dans le gabarit.
    """
    return render(request, "home.html")
