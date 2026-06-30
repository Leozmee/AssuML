"""
Modèles ORM SQLAlchemy 2.0 — AssuML.

Chaque classe correspond exactement à une table de database/schema.sql.
Les relations entre tables sont définies via relationship() pour les jointures ORM.
Les contraintes CHECK sont dupliquées ici pour la cohérence avec le schéma SQL.
"""

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Classe de base pour tous les modèles ORM AssuML."""

    pass


class Region(Base):
    """Référentiel des 4 régions géographiques USA."""

    __tablename__ = "regions"
    __table_args__ = (
        CheckConstraint(
            "nom_region IN ('southwest', 'southeast', 'northwest', 'northeast')",
            name="chk_regions_nom",
        ),
    )

    region_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom_region: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    # Relations
    clients: Mapped[List["Client"]] = relationship(back_populates="region")
    donnees_meteo: Mapped[List["DonneesMeteo"]] = relationship(back_populates="region")


class Client(Base):
    """Profil assuré — soft delete via date_suppression."""

    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint("age BETWEEN 18 AND 120", name="chk_clients_age"),
        CheckConstraint("sexe IN ('homme', 'femme')", name="chk_clients_sexe"),
        CheckConstraint("imc BETWEEN 10.00 AND 80.00", name="chk_clients_imc"),
        CheckConstraint("enfants >= 0", name="chk_clients_enfants"),
    )

    client_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.region_id", ondelete="CASCADE"), nullable=False
    )
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sexe: Mapped[str] = mapped_column(String(10), nullable=False)
    imc: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    enfants: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fumeur: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    a_un_compte: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    telephone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_creation: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    date_suppression: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Relations
    region: Mapped["Region"] = relationship(back_populates="clients")
    predictions: Mapped[List["Prediction"]] = relationship(back_populates="client")
    contrats: Mapped[List["Contrat"]] = relationship(back_populates="client")


class Prediction(Base):
    """Résultat d'une prédiction ML pour un client."""

    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint("score_risque BETWEEN 0 AND 1", name="chk_predictions_score"),
        CheckConstraint(
            "categorie_risque IN ('faible', 'moyen', 'eleve', 'critique')",
            name="chk_predictions_categorie",
        ),
        CheckConstraint(
            "decision IN ('accepter', 'refuser', 'examiner')",
            name="chk_predictions_decision",
        ),
    )

    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clients.client_id", ondelete="CASCADE"), nullable=False
    )
    cout_predit: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    score_risque: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    categorie_risque: Mapped[Optional[str]] = mapped_column(String(20))
    decision: Mapped[Optional[str]] = mapped_column(String(20))
    prime: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    version_modele: Mapped[Optional[str]] = mapped_column(String(60))
    date_prediction: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relations
    client: Mapped["Client"] = relationship(back_populates="predictions")


class Contrat(Base):
    """Contrat d'assurance souscrit par un client."""

    __tablename__ = "contrats"
    __table_args__ = (
        CheckConstraint(
            "statut IN ('actif', 'resilie', 'expire', 'suspendu')",
            name="chk_contrats_statut",
        ),
        CheckConstraint("prime_mensuelle > 0", name="chk_contrats_prime"),
        CheckConstraint(
            "type_couverture IN ('basique', 'standard', 'premium', 'famille')",
            name="chk_contrats_couverture",
        ),
        CheckConstraint(
            "date_fin IS NULL OR date_fin > date_debut",
            name="chk_contrats_dates",
        ),
    )

    contrat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clients.client_id", ondelete="CASCADE"), nullable=False
    )
    statut: Mapped[str] = mapped_column(String(20), nullable=False, default="actif")
    prime_mensuelle: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    date_debut: Mapped[date] = mapped_column(Date, nullable=False)
    date_fin: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    type_couverture: Mapped[str] = mapped_column(String(50), nullable=False)
    date_creation: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relations
    client: Mapped["Client"] = relationship(back_populates="contrats")


class DonneesMeteo(Base):
    """Données météo par région et par saison — source API OpenWeatherMap."""

    __tablename__ = "donnees_meteo"
    __table_args__ = (
        CheckConstraint(
            "temperature_moy BETWEEN -50 AND 60", name="chk_meteo_temperature"
        ),
        CheckConstraint("humidite_moy BETWEEN 0 AND 100", name="chk_meteo_humidite"),
        CheckConstraint("precipitations >= 0", name="chk_meteo_precipitations"),
        CheckConstraint(
            "saison IN ('printemps', 'ete', 'automne', 'hiver')",
            name="chk_meteo_saison",
        ),
    )

    meteo_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.region_id", ondelete="CASCADE"), nullable=False
    )
    temperature_moy: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    humidite_moy: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    precipitations: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    saison: Mapped[str] = mapped_column(String(20), nullable=False)
    date_collecte: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relations
    region: Mapped["Region"] = relationship(back_populates="donnees_meteo")


class Article(Base):
    """Article de presse scrappé sur la santé et l'assurance."""

    __tablename__ = "articles"

    article_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titre: Mapped[str] = mapped_column(String(500), nullable=False)
    url_source: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    nom_source: Mapped[str] = mapped_column(String(100), nullable=False)
    resume: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_publication: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    date_scraping: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
