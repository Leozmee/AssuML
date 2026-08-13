"""
Fonctions CRUD — AssuML.

Opérations de base sur les entités principales :
  - Client       : create, get, list, update, soft_delete
  - Prediction   : create, list par client
  - Contrat      : create

Toutes les fonctions reçoivent une session SQLAlchemy (db) en premier argument.
Le soft delete utilise date_suppression — jamais de DELETE physique sur les clients.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database.models import Article, Client, Contrat, DonneesMeteo, Prediction


# ── Client ────────────────────────────────────────────────────────────────────


def create_client(
    db: Session,
    age: int,
    sexe: str,
    imc: float,
    enfants: int,
    fumeur: bool,
    region_id: int,
    nom: Optional[str] = None,
    prenom: Optional[str] = None,
    email: Optional[str] = None,
    telephone: Optional[str] = None,
    a_un_compte: bool = False,
) -> Client:
    """Crée un nouveau client et le persiste en base.

    Args:
        db: Session SQLAlchemy active.
        age: Âge en années (18-120).
        sexe: 'homme' ou 'femme'.
        imc: Indice de masse corporelle (10.00-80.00).
        enfants: Nombre d'enfants à charge (>= 0).
        fumeur: True si le client est fumeur.
        region_id: FK vers la table regions.
        nom: Nom de famille (optionnel — absent pour les clients seedés).
        prenom: Prénom (optionnel — absent pour les clients seedés).
        email: Adresse e-mail (optionnel).
        telephone: Numéro de téléphone (optionnel).
        a_un_compte: True si le client a créé un compte utilisateur.

    Returns:
        Client: Instance persistée avec client_id assigné.
    """
    client = Client(
        age=age,
        sexe=sexe,
        imc=imc,
        enfants=enfants,
        fumeur=fumeur,
        region_id=region_id,
        nom=nom,
        prenom=prenom,
        email=email,
        telephone=telephone,
        a_un_compte=a_un_compte,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def get_client(db: Session, client_id: int) -> Optional[Client]:
    """Récupère un client par son identifiant primaire.

    Args:
        db: Session SQLAlchemy active.
        client_id: Clé primaire du client.

    Returns:
        Client si trouvé, None sinon.
    """
    return db.query(Client).filter(Client.client_id == client_id).first()


def get_clients(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    actifs_only: bool = True,
) -> list[Client]:
    """Retourne une liste paginée de clients.

    Args:
        db: Session SQLAlchemy active.
        skip: Nombre d'enregistrements à ignorer (pagination).
        limit: Nombre maximum d'enregistrements retournés.
        actifs_only: Si True, exclut les clients avec date_suppression définie.

    Returns:
        Liste de clients.
    """
    query = db.query(Client)
    if actifs_only:
        query = query.filter(Client.date_suppression.is_(None))
    return query.order_by(Client.client_id).offset(skip).limit(limit).all()


def update_client(
    db: Session,
    client_id: int,
    **kwargs,
) -> Optional[Client]:
    """Met à jour les champs d'un client existant.

    Seuls les champs fournis en kwargs sont mis à jour.
    Les champs non mentionnés restent inchangés.

    Args:
        db: Session SQLAlchemy active.
        client_id: Clé primaire du client à modifier.
        **kwargs: Champs à mettre à jour (age, sexe, imc, enfants,
                  fumeur, email, telephone).

    Returns:
        Client mis à jour, ou None si client_id inexistant.
    """
    client = get_client(db, client_id)
    if client is None:
        return None
    for key, value in kwargs.items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


def soft_delete_client(db: Session, client_id: int) -> Optional[Client]:
    """Marque un client comme supprimé (soft delete).

    Définit date_suppression à l'horodatage courant.
    Le client reste physiquement en base — jamais de DELETE.

    Args:
        db: Session SQLAlchemy active.
        client_id: Clé primaire du client à supprimer logiquement.

    Returns:
        Client avec date_suppression définie, ou None si client_id inexistant.
    """
    client = get_client(db, client_id)
    if client is None:
        return None
    client.date_suppression = datetime.now()
    db.commit()
    db.refresh(client)
    return client


# ── Prediction ────────────────────────────────────────────────────────────────


def create_prediction(
    db: Session,
    client_id: int,
    cout_predit: Optional[float],
    score_risque: Optional[float],
    categorie_risque: Optional[str],
    decision: Optional[str],
    prime: Optional[float],
    version_modele: Optional[str],
) -> Prediction:
    """Crée une prédiction ML pour un client.

    Args:
        db: Session SQLAlchemy active.
        client_id: FK vers la table clients.
        cout_predit: Coût médical prédit en USD.
        score_risque: Score de risque entre 0 et 1.
        categorie_risque: 'faible', 'moyen', 'eleve' ou 'critique'.
        decision: 'accepter', 'refuser' ou 'examiner'.
        prime: Prime d'assurance calculée en USD.
        version_modele: Version du modèle ML utilisé.

    Returns:
        Prediction: Instance persistée avec prediction_id assigné.
    """
    prediction = Prediction(
        client_id=client_id,
        cout_predit=cout_predit,
        score_risque=score_risque,
        categorie_risque=categorie_risque,
        decision=decision,
        prime=prime,
        version_modele=version_modele,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def get_predictions_by_client(db: Session, client_id: int) -> list[Prediction]:
    """Retourne toutes les prédictions associées à un client.

    Args:
        db: Session SQLAlchemy active.
        client_id: FK vers la table clients.

    Returns:
        Liste de Prediction (peut être vide si aucune prédiction).
    """
    return db.query(Prediction).filter(Prediction.client_id == client_id).all()


def get_last_prediction_by_client(db: Session, client_id: int) -> Optional[Prediction]:
    """Retourne la prédiction la plus récente d'un client, ou None.

    Args:
        db: Session SQLAlchemy active.
        client_id: FK vers la table clients.

    Returns:
        Dernière Prediction ou None si aucune n'existe.
    """
    return (
        db.query(Prediction)
        .filter(Prediction.client_id == client_id)
        .order_by(Prediction.date_prediction.desc())
        .first()
    )


# ── Contrat ───────────────────────────────────────────────────────────────────


def create_contrat(
    db: Session,
    client_id: int,
    statut: str,
    prime_mensuelle: float,
    date_debut,
    type_couverture: str,
    date_fin=None,
) -> Contrat:
    """Crée un contrat d'assurance pour un client.

    Args:
        db: Session SQLAlchemy active.
        client_id: FK vers la table clients.
        statut: 'actif', 'resilie', 'expire' ou 'suspendu'.
        prime_mensuelle: Montant mensuel en USD (> 0).
        date_debut: Date de début du contrat (date ou datetime).
        type_couverture: 'basique', 'standard', 'premium' ou 'famille'.
        date_fin: Date de fin optionnelle (doit être > date_debut).

    Returns:
        Contrat: Instance persistée avec contrat_id assigné.
    """
    contrat = Contrat(
        client_id=client_id,
        statut=statut,
        prime_mensuelle=prime_mensuelle,
        date_debut=date_debut,
        type_couverture=type_couverture,
        date_fin=date_fin,
    )
    db.add(contrat)
    db.commit()
    db.refresh(contrat)
    return contrat


# ── Contrat (lecture + mise à jour) ──────────────────────────────────────────


def get_contrat(db: Session, contrat_id: int) -> Optional[Contrat]:
    """Récupère un contrat par son identifiant.

    Args:
        db: Session SQLAlchemy active.
        contrat_id: Clé primaire du contrat.

    Returns:
        Contrat si trouvé, None sinon.
    """
    return db.query(Contrat).filter(Contrat.contrat_id == contrat_id).first()


def get_contrats(
    db: Session,
    client_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Contrat]:
    """Retourne une liste paginée de contrats, avec filtre optionnel par client.

    Args:
        db: Session SQLAlchemy active.
        client_id: Si fourni, filtre les contrats de ce client uniquement.
        skip: Décalage pagination.
        limit: Nombre maximum de résultats.

    Returns:
        Liste de Contrat.
    """
    query = db.query(Contrat)
    if client_id is not None:
        query = query.filter(Contrat.client_id == client_id)
    return query.offset(skip).limit(limit).all()


def update_contrat_statut(
    db: Session, contrat_id: int, statut: str
) -> Optional[Contrat]:
    """Modifie le statut d'un contrat existant.

    Args:
        db: Session SQLAlchemy active.
        contrat_id: Clé primaire du contrat.
        statut: Nouveau statut — 'actif', 'resilie', 'expire' ou 'suspendu'.

    Returns:
        Contrat mis à jour, ou None si contrat_id inexistant.
    """
    contrat = get_contrat(db, contrat_id)
    if contrat is None:
        return None
    contrat.statut = statut
    db.commit()
    db.refresh(contrat)
    return contrat


def update_contrat_prime(
    db: Session, contrat_id: int, prime_mensuelle: float
) -> Optional[Contrat]:
    """Met à jour la prime mensuelle d'un contrat existant."""
    contrat = get_contrat(db, contrat_id)
    if contrat is None:
        return None
    contrat.prime_mensuelle = prime_mensuelle
    db.commit()
    db.refresh(contrat)
    return contrat


def update_contrat_type(
    db: Session, contrat_id: int, type_couverture: str
) -> Optional[Contrat]:
    """Met à jour le type de couverture d'un contrat existant."""
    contrat = get_contrat(db, contrat_id)
    if contrat is None:
        return None
    contrat.type_couverture = type_couverture
    db.commit()
    db.refresh(contrat)
    return contrat


# ── Article et DonneesMeteo (lecture seule) ───────────────────────────────────


def get_articles(
    db: Session,
    source: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Article], int]:
    """Retourne les articles avec filtre optionnel par source.

    Args:
        db: Session SQLAlchemy active.
        source: Filtre sur nom_source (correspondance exacte).
        skip: Décalage pagination.
        limit: Nombre maximum de résultats.

    Returns:
        Tuple (liste d'articles, total avant pagination).
    """
    query = db.query(Article)
    if source:
        query = query.filter(Article.nom_source == source)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def get_donnees_meteo(
    db: Session,
    region: Optional[str] = None,
    saison: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[DonneesMeteo]:
    """Retourne les données météo avec filtres optionnels.

    Args:
        db: Session SQLAlchemy active.
        region: Filtre sur nom_region via jointure regions.
        saison: Filtre sur saison ('hiver', 'printemps', 'ete', 'automne').
        skip: Décalage pagination.
        limit: Nombre maximum de résultats.

    Returns:
        Liste de DonneesMeteo.
    """
    from database.models import Region

    query = db.query(DonneesMeteo)
    if region:
        query = query.join(Region).filter(Region.nom_region == region)
    if saison:
        query = query.filter(DonneesMeteo.saison == saison)
    return query.offset(skip).limit(limit).all()
