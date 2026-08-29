"""Filtres template de formatage — partagés entre Analytics, Scoring et
Gestion clients (chargés via `{% load format_extras %}`)."""

from datetime import date, datetime

from django import template

register = template.Library()


@register.filter
def format_fr(valeur, decimales=0):
    """Formate un nombre en notation française : espace pour les milliers,
    virgule pour la décimale (ex. 5000000 → "5 000 000", 13454.0 avec
    decimales=2 → "13 454,00") — pour la lisibilité des grandes volumétries
    (Big Data, coûts moyens) sans dépendre d'un réglage global Django.
    """
    try:
        valeur = float(valeur)
    except (TypeError, ValueError):
        return valeur

    decimales = int(decimales)
    entier, _, decimale = f"{valeur:.{decimales}f}".partition(".")
    negatif = entier.startswith("-")
    entier = entier.lstrip("-")
    groupes = []
    while len(entier) > 3:
        groupes.insert(0, entier[-3:])
        entier = entier[:-3]
    groupes.insert(0, entier)
    entier_espace = " ".join(groupes)
    if negatif:
        entier_espace = "-" + entier_espace

    return f"{entier_espace},{decimale}" if decimales else entier_espace


@register.filter
def date_fr(valeur):
    """Formate une date en jj/mm/aaaa.

    Le filtre `date` de Django n'accepte qu'un objet date ; or les dates
    venues de l'API arrivent en chaîne ISO ("2026-08-12"). Ce filtre accepte
    les deux, et rend la valeur inchangée s'il ne sait pas l'interpréter.
    """
    if isinstance(valeur, (datetime, date)):
        return valeur.strftime("%d/%m/%Y")
    if not valeur:
        return valeur
    try:
        return datetime.fromisoformat(str(valeur)[:19]).strftime("%d/%m/%Y")
    except ValueError:
        return valeur
