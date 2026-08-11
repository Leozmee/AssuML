"""
Scraper santemagazine.fr — AssuML ETL.

Approche en 2 passes :
  1. Page listing (/actualites) → URLs des vrais articles
  2. Visite de chaque article → métadonnées OG (titre H1, résumé, date)

Les URLs de catégories (ex. /actualites/actualites-sante) sont exclues.
Seuls les articles avec un slug numérique ou textuel long sont retenus.

Flux :
  listing → liste d'URLs → visite individuelle → backup JSON → transform → insertion BDD

Usage standalone :
    python -m data_pipeline.extract.scraper
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Ajouter la racine du projet au PYTHONPATH
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from data_pipeline.load.db_loader import (  # noqa: E402
    compter_enregistrements,
    insert_articles,
)
from data_pipeline.transform.transform_articles import (  # noqa: E402
    transformer_articles,
)

URL_LISTING = "https://www.santemagazine.fr/actualites"
BASE_URL = "https://www.santemagazine.fr"
NOM_SOURCE = "santemagazine.fr"
DOSSIER_BACKUP = ROOT / "data" / "external" / "scraped_data"

# Nombre maximum d'articles à visiter par exécution (évite la surcharge)
MAX_ARTICLES = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Pattern des URLs d'articles réels (sous-catégorie + slug avec contenu)
# Exemple valide : /actualites/actualites-sante/mon-article-1234567
# Exemple exclu  : /actualites/actualites-sante  (juste une catégorie)
RE_ARTICLE = re.compile(r"^/actualites/actualites-[a-z-]+/[a-z0-9][a-z0-9-]{10,}")


def _get(url: str, timeout: int = 10) -> Optional[requests.Response]:
    """Effectue une requête GET avec gestion des erreurs réseau.

    Args:
        url: URL à récupérer.
        timeout: Délai maximum en secondes.

    Returns:
        Response si succès (status 200), None sinon.
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r
        return None
    except requests.exceptions.RequestException:
        return None


def extraire_urls_listing(url: str = URL_LISTING) -> list[str]:
    """Récupère les URLs des vrais articles depuis la page listing.

    Filtre les liens de catégories et ne garde que les slugs d'articles
    (pattern : /actualites/actualites-{categorie}/{slug-long}).

    Args:
        url: URL de la page listing.

    Returns:
        list[str]: URLs absolues des articles, dédupliquées.
    """
    response = _get(url)
    if response is None:
        print(f"  ERREUR : impossible de charger {url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    vus = set()
    urls = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if RE_ARTICLE.match(href) and href not in vus:
            vus.add(href)
            urls.append(urljoin(BASE_URL, href))

    return urls


def scraper_article(url: str) -> Optional[dict]:
    """Visite une page d'article et extrait titre, contenu complet et date.

    Priorité d'extraction :
      - Titre   : balise H1 → og:title
      - Contenu : div.article-content (corps complet) → og:description (fallback)
      - Date    : article:published_time → og:updated_time → <time>

    Le contenu complet est stocké dans le champ 'resume' (TEXT illimité en PG).

    Args:
        url: URL absolue de l'article.

    Returns:
        dict avec clés titre/url_source/nom_source/resume/date_publication_str,
        ou None si la page est inaccessible ou vide.
    """
    response = _get(url)
    if response is None:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Titre : H1 en priorité, og:title en fallback
    h1 = soup.find("h1")
    titre = h1.get_text(separator=" ", strip=True) if h1 else ""
    titre = re.sub(r"\s+", " ", titre).strip()
    if not titre:
        og_title = soup.find("meta", property="og:title")
        titre = og_title["content"].strip() if og_title else ""

    if not titre or titre.lower() in ("page introuvable", "erreur 404"):
        return None  # Article inaccessible

    # Contenu complet : div.article-content → paragraphes du main → og:description
    contenu = ""
    article_div = soup.find("div", class_=lambda c: c and "article-content" in c)
    if article_div:
        # Supprimer les blocs publicitaires et navigation internes
        for tag in article_div.find_all(["script", "style", "aside", "nav", "figure"]):
            tag.decompose()
        paragraphes = [
            p.get_text(separator=" ", strip=True)
            for p in article_div.find_all("p")
            if len(p.get_text(strip=True)) > 30
        ]
        contenu = "\n\n".join(paragraphes)

    if not contenu:
        # Fallback : og:description (résumé court)
        og_desc = soup.find("meta", property="og:description")
        contenu = og_desc["content"].strip() if og_desc else ""

    # Image de l'article : og:image (image principale utilisée pour le partage social)
    og_image = soup.find("meta", property="og:image")
    image_url = (
        og_image["content"].strip() if og_image and og_image.get("content") else ""
    )

    # Date : article:published_time → og:updated_time → balise <time>
    date_str = ""
    og_pub = soup.find("meta", property="article:published_time")
    if og_pub and og_pub.get("content"):
        date_str = og_pub["content"]
    else:
        og_upd = soup.find("meta", property="og:updated_time")
        if og_upd and og_upd.get("content"):
            date_str = og_upd["content"]
        else:
            time_tag = soup.find("time")
            if time_tag:
                date_str = time_tag.get("datetime", "") or time_tag.get_text(strip=True)

    return {
        "titre": titre,
        "url_source": url,
        "nom_source": NOM_SOURCE,
        "resume": contenu,
        "image_url": image_url,
        "date_publication_str": date_str,
    }


def scraper_articles(
    url_listing: str = URL_LISTING, max_articles: int = MAX_ARTICLES
) -> list[dict]:
    """Orchestre le scraping en 2 passes : listing puis visite individuelle.

    Args:
        url_listing: URL de la page listing d'actualités.
        max_articles: Nombre maximum d'articles à visiter.

    Returns:
        list[dict]: Articles bruts avec titre, URL, résumé et date.
    """
    # Passe 1 : récupérer les URLs
    urls = extraire_urls_listing(url_listing)
    print(f"  {len(urls)} URLs d'articles trouvées sur le listing")

    if not urls:
        return []

    # Passe 2 : visiter chaque article
    articles = []
    for i, url in enumerate(urls[:max_articles], 1):
        print(f"  [{i}/{min(len(urls), max_articles)}] {url[-60:]}")
        article = scraper_article(url)
        if article:
            articles.append(article)
        time.sleep(0.5)  # Politesse réseau — 500ms entre chaque requête

    return articles


def sauvegarder_backup(articles: list[dict], dossier: Path) -> str:
    """Sauvegarde les articles bruts dans un fichier JSON horodaté.

    Args:
        articles: Liste d'articles bruts à sauvegarder.
        dossier: Répertoire de backup.

    Returns:
        str: Chemin absolu du fichier créé.
    """
    dossier.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin = dossier / f"articles_{horodatage}.json"
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    return str(chemin)


def main() -> None:
    """Orchestration complète du pipeline scraping.

    Étapes :
      1. Scraping en 2 passes (listing + articles individuels)
      2. Sauvegarde JSON horodatée
      3. Transformation (nettoyage, normalisation dates, déduplication)
      4. Insertion dans articles (ON CONFLICT DO NOTHING)
      5. Rapport
    """
    print("=" * 55)
    print("ETL Scraping — santemagazine.fr → articles")
    print("=" * 55)

    # Étape 1 : scraping
    print(f"\n[1/4] Scraping de {URL_LISTING}...")
    articles_bruts = scraper_articles()
    print(f"  {len(articles_bruts)} articles avec contenu récupérés")

    if not articles_bruts:
        print("  Aucun article récupéré — vérifier la connexion réseau.")
        return

    # Étape 2 : backup
    chemin_backup = sauvegarder_backup(articles_bruts, DOSSIER_BACKUP)
    print(f"\n[2/4] Backup sauvegardé : {chemin_backup}")

    # Étape 3 : transformation
    articles_propres = transformer_articles(articles_bruts)
    print(f"\n[3/4] Transformation : {len(articles_propres)} articles valides")

    # Étape 4 : insertion
    n_inseres = insert_articles(articles_propres)
    print(
        f"[4/4] Insertion : {n_inseres} article(s) nouveau(x) "
        f"inséré(s) (doublons ignorés)"
    )

    # Rapport
    total = compter_enregistrements("articles")
    print(f"\n  Total en base : {total} article(s) dans articles")
    print("=" * 55)


if __name__ == "__main__":
    main()
