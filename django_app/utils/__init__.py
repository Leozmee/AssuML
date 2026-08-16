"""Utilitaires partagés AssuML Django."""

# Coefficients de marge par catégorie de risque (cohérents avec
# business/scoring.py) — partagés entre le scoring d'un client existant
# (gestion) et la simulation libre (scoring).
COEFFICIENTS = {"faible": 1.20, "moyen": 1.35, "eleve": 1.50, "critique": 1.80}

# Mapping région nom ↔ region_id (correspond à l'ordre INSERT dans schema.sql)
REGION_ID_MAP = {
    "southwest": 1,
    "southeast": 2,
    "northwest": 3,
    "northeast": 4,
}

REGION_NOM_MAP = {v: k for k, v in REGION_ID_MAP.items()}


def region_nom_to_id(nom: str) -> int:
    """Convertit un nom de région en region_id (FK PostgreSQL)."""
    return REGION_ID_MAP[nom]


def region_id_to_nom(region_id: int) -> str:
    """Convertit un region_id en nom lisible."""
    return REGION_NOM_MAP.get(region_id, str(region_id))


def capitaliser_nom(valeur: str) -> str:
    """Met en majuscule la première lettre d'un nom/prénom (reste inchangé)."""
    valeur = (valeur or "").strip()
    return valeur[:1].upper() + valeur[1:] if valeur else valeur


def client_identite(client: dict) -> str:
    """Nom lisible d'un client pour les aria-label (ex. boutons d'action).

    "Prénom Nom" si renseignés, sinon "client <id>" (clients seedés sans
    nom/prénom) — évite l'ambiguïté entre lignes similaires d'un tableau
    pour les technologies d'assistance.
    """
    nom = (client.get("nom") or "").strip()
    prenom = (client.get("prenom") or "").strip()
    if nom or prenom:
        return f"{prenom} {nom}".strip()
    return f"client {client['client_id']}"


# Taille de référence utilisée pour reconstruire un couple (taille, poids)
# plausible à partir d'un IMC — la base ne stocke jamais taille/poids
# séparément (seulement `imc`), donc un formulaire qui ne connaît que
# l'IMC (ex. modification d'un client existant, sélection dans Simulation
# ML) doit inventer une paire qui redonne exactement le même IMC une fois
# recalculée. Ce n'est PAS la vraie taille/poids du client.
TAILLE_REF_CM = 170


def imc_vers_poids_taille(imc: float) -> tuple:
    """Reconstruit (taille, poids) à partir d'un IMC — voir TAILLE_REF_CM."""
    poids = round(float(imc) * (TAILLE_REF_CM / 100) ** 2, 1)
    return TAILLE_REF_CM, poids


def client_to_predict_payload(client: dict) -> dict:
    """Convertit un client (dict retourné par l'API) en payload /predict/*.

    Encode sexe/fumeur en 0/1 et la région en nom, au format attendu par
    PredictRequest côté FastAPI. N'inclut jamais client_id : à ajouter par
    l'appelant uniquement si la prédiction doit être persistée (cf.
    /predict/complet, qui ne sauvegarde que si client_id est fourni).
    """
    return {
        "age": client["age"],
        "sexe": 0 if client["sexe"] == "homme" else 1,
        "imc": float(client["imc"]),
        "enfants": client["enfants"],
        "fumeur": 1 if client["fumeur"] else 0,
        "region": region_id_to_nom(client["region_id"]),
    }


def filtrer_trier_clients(clients, sort="id_asc", compte="", contrat_filtre=""):
    """Filtre et trie une liste de clients — partagé entre gestion et scoring.

    Attend des clients déjà enrichis (`contrat` et `categorie_risque`
    présents). Réplique les 3 filtres de la liste "Gestion clients" (tri,
    statut de compte, statut de contrat) pour être réutilisable ailleurs
    (le sélecteur de client de Simulation ML).
    """
    if compte == "oui":
        clients = [c for c in clients if c.get("a_un_compte")]
    elif compte == "non":
        clients = [c for c in clients if not c.get("a_un_compte")]

    if contrat_filtre == "oui":
        clients = [
            c for c in clients if c.get("contrat") and c["contrat"]["statut"] == "actif"
        ]
    elif contrat_filtre == "non":
        clients = [
            c
            for c in clients
            if not c.get("contrat") or c["contrat"]["statut"] != "actif"
        ]

    risque_ordre = {"faible": 1, "moyen": 2, "eleve": 3, "critique": 4}
    if sort == "id_asc":
        clients.sort(key=lambda c: c["client_id"])
    elif sort == "id_desc":
        clients.sort(key=lambda c: c["client_id"], reverse=True)
    elif sort in ("risque_asc", "risque_desc"):
        # Les clients non scorés n'ont pas de valeur comparable : ils restent
        # toujours en fin de liste, quel que soit le sens du tri.
        scores = [c for c in clients if c.get("categorie_risque")]
        non_scores = [c for c in clients if not c.get("categorie_risque")]
        scores.sort(
            key=lambda c: risque_ordre.get(c["categorie_risque"], 0),
            reverse=(sort == "risque_desc"),
        )
        clients = scores + non_scores

    return clients


def enrichir_resultat_scoring(res: dict) -> dict:
    """Ajoute les champs dérivés (mensuel, marge, coefficient) au résultat API.

    Partagé entre le scoring d'un client existant (gestion) et la
    simulation libre (scoring) — les deux appelaient auparavant une copie
    identique de cette fonction.
    """
    res["cout_mensuel"] = round(res["cout_predit"] / 12, 2)
    res["prime_annuelle"] = res["prime"]
    res["prime_mensuelle"] = round(res["prime"] / 12, 2)
    res["marge_annuelle"] = round(res["prime"] - res["cout_predit"], 2)
    res["coefficient_marge"] = COEFFICIENTS.get(res["categorie_risque"], "—")
    return res
