"""
Client de métriques Railway — panneau Monitoring d'AssuML.

Interroge l'API GraphQL publique de Railway (backboard) pour alimenter quatre
graphiques du panneau Monitoring : latence, volume de requêtes, répartition des
codes de statut HTTP et consommation mémoire du service API.

Principe de conception : ce module ne lève jamais. Le panneau Monitoring est la
page montrée en démonstration ; elle doit rester affichable même si le jeton est
absent, si Railway est injoignable ou si la réponse change de forme. Toute
défaillance se traduit par des graphiques vides et un message, jamais par une
erreur 500.

Configuration (variables d'environnement) :
    RAILWAY_API_TOKEN                 Jeton de projet Railway
    RAILWAY_MONITORED_SERVICE_ID      Service à observer (celui de l'API)
    RAILWAY_MONITORED_ENVIRONMENT_ID  Environnement de ce service

Les deux derniers noms sont volontairement préfixés MONITORED : Railway injecte
automatiquement RAILWAY_SERVICE_ID et RAILWAY_ENVIRONMENT_ID dans chaque
service. Réutiliser ces noms ici ferait lire au conteneur Django ses propres
identifiants au lieu de ceux de l'API, et le panneau afficherait les métriques
du mauvais service sans que rien ne le signale.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
from django.conf import settings

URL_GRAPHQL = "https://backboard.railway.com/graphql/v2"

# Le panneau se rafraîchit toutes les 10 s : une requête lente bloquerait le
# rendu de toute la page. Mieux vaut un graphique vide qu'une page qui rame.
TIMEOUT_S = 8

# Fenêtre observée et granularité des points.
FENETRE_MINUTES = 60
PAS_SECONDES = 60


def _config() -> tuple[str, str, str] | None:
    """Retourne (jeton, service_id, environment_id), ou None si incomplet."""
    jeton = os.getenv("RAILWAY_API_TOKEN", "").strip()
    service = os.getenv("RAILWAY_MONITORED_SERVICE_ID", "").strip()
    environnement = os.getenv("RAILWAY_MONITORED_ENVIRONMENT_ID", "").strip()
    if not (jeton and service and environnement):
        return None
    return jeton, service, environnement


def est_configure() -> bool:
    """Indique si les trois variables d'environnement sont renseignées."""
    return _config() is not None


# En-têtes d'authentification, dans l'ordre d'essai. Railway attend
# `Project-Access-Token` pour un jeton de projet et `Authorization: Bearer`
# pour un jeton de compte, et REJETTE la requête si le mauvais est présent —
# les poser tous les deux simultanément échoue. On essaie donc le premier,
# puis l'autre, et on retient celui qui a répondu pour ne pas payer deux
# requêtes à chaque appel.
_ENTETES = (
    lambda jeton: {"Project-Access-Token": jeton},
    lambda jeton: {"Authorization": f"Bearer {jeton}"},
)

_entete_retenu: int | None = None


def _tenter(requete: str, variables: dict, jeton: str, index: int) -> dict | None:
    """Exécute la requête avec l'en-tête d'authentification numéro `index`."""
    try:
        reponse = requests.post(
            URL_GRAPHQL,
            json={"query": requete, "variables": variables},
            headers={"Content-Type": "application/json", **_ENTETES[index](jeton)},
            timeout=TIMEOUT_S,
        )
        charge = reponse.json()
    except (requests.RequestException, ValueError):
        return None
    if charge.get("errors") or charge.get("data") is None:
        return None
    return charge["data"]


def _interroger(requete: str, variables: dict) -> dict | None:
    """Exécute une requête GraphQL Railway. Retourne les données, ou None.

    Le type de jeton n'a pas à être déclaré par l'exploitant : le premier appel
    détermine quel en-tête Railway accepte, les suivants réutilisent ce choix.

    Args:
        requete: Document GraphQL.
        variables: Variables de la requête.

    Returns:
        dict | None: Le contenu de `data`, ou None en cas d'échec quelconque.
    """
    global _entete_retenu

    config = _config()
    if config is None:
        return None
    jeton, _, _ = config

    if _entete_retenu is not None:
        return _tenter(requete, variables, jeton, _entete_retenu)

    for index in range(len(_ENTETES)):
        data = _tenter(requete, variables, jeton, index)
        if data is not None:
            _entete_retenu = index
            return data
    return None


def _fenetre() -> dict:
    """Construit les bornes temporelles communes aux quatre requêtes.

    Les clés portent les noms des variables GraphQL déclarées dans les
    requêtes (`$d` et `$f`), pas ceux des arguments Railway : une variable
    absente fait échouer la requête avec un laconique « Problem processing
    request », sans indiquer laquelle manque.
    """
    fin = datetime.now(timezone.utc)
    debut = fin - timedelta(minutes=FENETRE_MINUTES)
    return {
        "d": debut.isoformat().replace("+00:00", "Z"),
        "f": fin.isoformat().replace("+00:00", "Z"),
    }


def _instant(ts: int) -> str:
    """Convertit un horodatage Unix en date locale lisible par Plotly.

    Deux exigences se rejoignent ici. D'abord l'heure locale plutôt qu'UTC :
    un utilisateur lit « 12:01 », pas « 10:01 » suivi d'une conversion mentale.
    Ensuite le format date complet : passé en simple libellé « 12:01 », Plotly
    traite l'axe comme une suite de catégories et affiche les soixante et une
    étiquettes de l'heure, qui se chevauchent. Une vraie date lui permet
    d'espacer les graduations lui-même.
    """
    return (
        datetime.fromtimestamp(ts, tz=timezone.utc)
        .astimezone(ZoneInfo(settings.TIME_ZONE))
        .strftime("%Y-%m-%d %H:%M:%S")
    )


def _horodatages(echantillons: list[dict]) -> list[str]:
    """Convertit une série d'échantillons en abscisses temporelles."""
    return [_instant(e["ts"]) for e in echantillons]


def _famille_statut(code: int) -> str:
    """Regroupe un code HTTP en famille affichable (2xx, 4xx, 5xx...)."""
    return f"{code // 100}xx"


# ── Les quatre graphiques ─────────────────────────────────────────────────────

_REQ_LATENCE = """
query($s:String!,$e:String!,$d:DateTime!,$f:DateTime!,$p:Int){
  httpDurationMetrics(serviceId:$s, environmentId:$e, startDate:$d,
                      endDate:$f, stepSeconds:$p){
    samples { ts p50 p95 p99 }
  }
}
"""

_REQ_REQUETES = """
query($s:String!,$e:String!,$d:DateTime!,$f:DateTime!,$p:Int){
  httpMetrics(serviceId:$s, environmentId:$e, startDate:$d,
              endDate:$f, stepSeconds:$p){
    samples { ts value }
  }
}
"""

_REQ_STATUTS = """
query($s:String!,$e:String!,$d:DateTime!,$f:DateTime!,$p:Int){
  httpMetricsGroupedByStatus(serviceId:$s, environmentId:$e, startDate:$d,
                             endDate:$f, stepSeconds:$p){
    statusCode
    samples { ts value }
  }
}
"""

_REQ_MEMOIRE = """
query($s:String!,$e:String!,$d:DateTime!,$f:DateTime!,$p:Int){
  metrics(serviceId:$s, environmentId:$e, startDate:$d, endDate:$f,
          sampleRateSeconds:$p,
          measurements:[MEMORY_USAGE_GB, MEMORY_LIMIT_GB]){
    measurement
    values { ts value }
  }
}
"""


def _variables() -> dict | None:
    """Assemble les variables communes aux quatre requêtes."""
    config = _config()
    if config is None:
        return None
    _, service, environnement = config
    return {"s": service, "e": environnement, "p": PAS_SECONDES, **_fenetre()}


def latence() -> list[dict]:
    """Latence des réponses HTTP, en percentiles.

    Les percentiles priment sur une moyenne : celle-ci masque les requêtes
    lentes, alors qu'un p99 élevé face à un p50 bas révèle qu'une minorité
    d'appels souffre.

    Returns:
        list[dict]: Trois traces Plotly (p50, p95, p99), ou liste vide.
    """
    variables = _variables()
    if variables is None:
        return []
    data = _interroger(_REQ_LATENCE, variables)
    if not data:
        return []
    echantillons = (data.get("httpDurationMetrics") or {}).get("samples") or []
    if not echantillons:
        return []

    abscisses = _horodatages(echantillons)
    # Railway renvoie déjà des millisecondes : aucune conversion. Vérifié sur
    # des relevés réels (p50 autour de 15 à 37), une lecture en secondes
    # donnerait des latences de plusieurs dizaines de secondes, absurdes.
    # "lines+markers" et non "lines" seul : Railway n'émet un échantillon que
    # pour les minutes ayant reçu du trafic. Sur un service peu sollicité, les
    # points sont rares et distants, et un trait continu laisserait croire à
    # une évolution progressive entre deux mesures qui n'ont rien entre elles.
    # Les marqueurs montrent où se trouvent les relevés réels.
    return [
        {
            "type": "scatter",
            "mode": "lines+markers",
            "name": nom,
            "x": abscisses,
            "y": [round(e.get(cle) or 0, 1) for e in echantillons],
        }
        for cle, nom in (
            ("p50", "Médiane (p50)"),
            ("p95", "p95 — 5 % plus lentes"),
            ("p99", "p99 — 1 % plus lentes"),
        )
    ]


def requetes() -> list[dict]:
    """Volume de requêtes HTTP reçues par le service — le trafic de l'app.

    Returns:
        list[dict]: Une trace Plotly en barres, ou liste vide.
    """
    variables = _variables()
    if variables is None:
        return []
    data = _interroger(_REQ_REQUETES, variables)
    if not data:
        return []
    echantillons = (data.get("httpMetrics") or {}).get("samples") or []
    if not echantillons:
        return []

    return [
        {
            "type": "bar",
            "name": "Requêtes",
            "x": _horodatages(echantillons),
            "y": [e.get("value") or 0 for e in echantillons],
        }
    ]


def codes_statut() -> list[dict]:
    """Répartition des réponses par famille de code HTTP.

    Railway renvoie une série par code exact (200, 401, 500...). Les codes sont
    regroupés par famille : une dizaine de courbes serait illisible, alors que
    la distinction 2xx / 4xx / 5xx suffit à lire un incident.

    Returns:
        list[dict]: Une trace Plotly par famille rencontrée, ou liste vide.
    """
    variables = _variables()
    if variables is None:
        return []
    data = _interroger(_REQ_STATUTS, variables)
    if not data:
        return []
    series = data.get("httpMetricsGroupedByStatus") or []
    if not series:
        return []

    # Somme des valeurs par (famille, horodatage)
    par_famille: dict[str, dict[int, float]] = {}
    for serie in series:
        code = serie.get("statusCode")
        if code is None:
            continue
        famille = _famille_statut(code)
        cumul = par_famille.setdefault(famille, {})
        for e in serie.get("samples") or []:
            cumul[e["ts"]] = cumul.get(e["ts"], 0) + (e.get("value") or 0)

    if not par_famille:
        return []

    horodatages = sorted({ts for cumul in par_famille.values() for ts in cumul})
    abscisses = [_instant(ts) for ts in horodatages]
    couleurs = {"2xx": "#2e9e5b", "3xx": "#2f6a9c", "4xx": "#d99126", "5xx": "#c0392b"}
    # Le code seul ne parle qu'aux initiés : on nomme ce qu'il signifie.
    sens = {
        "2xx": "2xx — Succès",
        "3xx": "3xx — Redirection",
        "4xx": "4xx — Erreur du client",
        "5xx": "5xx — Erreur du serveur",
    }

    return [
        {
            "type": "bar",
            "name": sens.get(famille, famille),
            "x": abscisses,
            "y": [cumul.get(ts, 0) for ts in horodatages],
            "marker": {"color": couleurs.get(famille, "#516980")},
        }
        for famille, cumul in sorted(par_famille.items())
    ]


def memoire() -> list[dict]:
    """Mémoire consommée par le conteneur, tracée face à sa limite.

    La limite est tracée avec l'usage : une courbe seule ne dit pas s'il reste
    de la marge. Un usage qui rejoint le plafond annonce un arrêt du conteneur
    pour dépassement mémoire, qui se manifeste côté client par un 503.

    Returns:
        list[dict]: Deux traces Plotly (usage, limite) en mégaoctets, ou vide.
    """
    variables = _variables()
    if variables is None:
        return []
    data = _interroger(_REQ_MEMOIRE, variables)
    if not data:
        return []
    series = data.get("metrics") or []
    if not series:
        return []

    libelles = {
        "MEMORY_USAGE_GB": ("Mémoire utilisée", "lines"),
        "MEMORY_LIMIT_GB": ("Limite allouée", "lines"),
    }
    # La mémoire est relevée en continu, elle : un trait plein y est fidèle,
    # contrairement à la latence qui ne connaît que les minutes avec trafic.
    traces = []
    for serie in series:
        mesure = serie.get("measurement")
        valeurs = serie.get("values") or []
        if mesure not in libelles or not valeurs:
            continue
        nom, mode = libelles[mesure]
        # Railway renvoie des gigaoctets ; les mégaoctets se lisent mieux pour
        # un conteneur qui en consomme quelques centaines. Une valeur nulle sur
        # la limite n'est pas une limite de zéro mais une absence de relevé :
        # elle devient None, que Plotly rend par une interruption de la courbe
        # plutôt que par une chute jusqu'à l'axe.
        ordonnees = []
        for v in valeurs:
            brut = v.get("value") or 0
            if mesure == "MEMORY_LIMIT_GB" and brut == 0:
                ordonnees.append(None)
            else:
                ordonnees.append(round(brut * 1024, 1))
        trace = {
            "type": "scatter",
            "mode": mode,
            "name": nom,
            "x": _horodatages(valeurs),
            "y": ordonnees,
        }
        if mesure == "MEMORY_LIMIT_GB":
            trace["line"] = {"dash": "dash", "color": "#c0392b"}
        traces.append(trace)
    return traces


def graphiques() -> dict:
    """Assemble les quatre graphiques et leurs mises en page pour la vue.

    Returns:
        dict: {"configure": bool, "charts": {...}, "layouts": {...},
        "disponible": bool}. `charts` et `layouts` sont sérialisés en JSON,
        prêts pour le composant components/plotly_chart.html.
    """
    if not est_configure():
        return {"configure": False, "disponible": False, "charts": {}, "layouts": {}}

    brut = {
        "latence": latence(),
        "requetes": requetes(),
        "statuts": codes_statut(),
        "memoire": memoire(),
    }
    mises_en_page = {
        "latence": {
            "xaxis": {"title": "Heure", "type": "date", "tickformat": "%H:%M"},
            "yaxis": {"title": "Latence (ms)"},
            "showlegend": True,
        },
        "requetes": {
            "xaxis": {"title": "Heure", "type": "date", "tickformat": "%H:%M"},
            "yaxis": {"title": "Requêtes"},
        },
        "statuts": {
            "xaxis": {"title": "Heure", "type": "date", "tickformat": "%H:%M"},
            "yaxis": {"title": "Réponses"},
            "barmode": "stack",
            "showlegend": True,
        },
        "memoire": {
            "xaxis": {"title": "Heure", "type": "date", "tickformat": "%H:%M"},
            "yaxis": {"title": "Mémoire (Mo)"},
            "showlegend": True,
        },
    }

    return {
        "configure": True,
        "disponible": any(brut.values()),
        "charts": {cle: json.dumps(valeur) for cle, valeur in brut.items()},
        "layouts": {cle: json.dumps(valeur) for cle, valeur in mises_en_page.items()},
    }
