"""
Transformation des articles scrappés — AssuML ETL.

Fonctions :
  - nettoyer_html()        : supprime les balises HTML, normalise les espaces
  - normaliser_date()      : parse une chaîne de date en datetime ou None
  - transformer_articles() : pipeline complet de nettoyage + déduplication

Aucune dépendance à la base de données — module de transformation pur.
"""

import re
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup


# Formats de dates tentés dans l'ordre
FORMATS_DATE = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d %B %Y",
    "%d %b %Y",
]

# Correspondances des mois français → mois anglais pour strptime
MOIS_FR = {
    "janvier": "January",
    "février": "February",
    "mars": "March",
    "avril": "April",
    "mai": "May",
    "juin": "June",
    "juillet": "July",
    "août": "August",
    "septembre": "September",
    "octobre": "October",
    "novembre": "November",
    "décembre": "December",
    "jan": "Jan",
    "fév": "Feb",
    "avr": "Apr",
    "juil": "Jul",
    "sep": "Sep",
    "oct": "Oct",
    "nov": "Nov",
    "déc": "Dec",
}


def nettoyer_html(texte: str) -> str:
    """Supprime toutes les balises HTML et normalise les espaces.

    Args:
        texte: Chaîne pouvant contenir du HTML brut.

    Returns:
        str: Texte brut nettoyé, sans balises ni espaces superflus.
    """
    if not texte:
        return ""
    soup = BeautifulSoup(texte, "html.parser")
    texte_brut = soup.get_text(separator=" ")
    # Normalisation des espaces multiples
    texte_brut = re.sub(r"\s+", " ", texte_brut).strip()
    return texte_brut


def normaliser_date(date_str: Optional[str]) -> Optional[datetime]:
    """Convertit une chaîne de date en objet datetime.

    Tente plusieurs formats courants, avec traduction des mois français.
    Retourne None si aucun format ne correspond plutôt que de générer
    une date incorrecte.

    Args:
        date_str: Chaîne de date brute (ex. '15 avril 2026', '2026-04-15').

    Returns:
        datetime si parseable, None sinon.
    """
    if not date_str or not date_str.strip():
        return None

    date_nettoyee = date_str.strip()

    # Traduction des mois français en anglais pour strptime
    date_en = date_nettoyee.lower()
    for fr, en in MOIS_FR.items():
        date_en = date_en.replace(fr, en)

    for fmt in FORMATS_DATE:
        try:
            dt = datetime.strptime(date_en, fmt)
            # Supprimer le timezone pour cohérence avec PostgreSQL TIMESTAMP
            return dt.replace(tzinfo=None)
        except ValueError:
            continue

    return None


def transformer_articles(articles_bruts: list[dict]) -> list[dict]:
    """Nettoie, normalise et déduplique une liste d'articles scrappés.

    Pipeline :
      1. Filtrage des articles sans titre ou URL
      2. Nettoyage HTML sur titre et résumé
      3. Normalisation de la date de publication
      4. Troncature du résumé à 2000 caractères
      5. Déduplication par url_source (garde le premier)

    Args:
        articles_bruts: Liste de dicts avec clés :
                        titre, url_source, nom_source, resume, date_publication_str

    Returns:
        list[dict]: Articles nettoyés prêts pour insert_articles(), avec clés :
                    titre, url_source, nom_source, resume, date_publication
    """
    vus = set()
    articles_propres = []

    for article in articles_bruts:
        # Filtrage des articles incomplets
        titre = nettoyer_html(article.get("titre", "")).strip()
        url = article.get("url_source", "").strip()

        if not titre or not url:
            continue

        # Déduplication par URL
        if url in vus:
            continue
        vus.add(url)

        # Nettoyage du résumé
        resume_brut = article.get("resume", "") or ""
        resume = nettoyer_html(resume_brut)  # TEXT illimité en PostgreSQL

        # Normalisation de la date
        date_pub = normaliser_date(article.get("date_publication_str"))

        articles_propres.append(
            {
                "titre": titre[:500],  # limite VARCHAR(500) du schéma
                "url_source": url,
                "nom_source": article.get("nom_source", ""),
                "resume": resume if resume else None,
                "date_publication": date_pub,
            }
        )

    return articles_propres
