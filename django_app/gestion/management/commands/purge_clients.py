"""Commande purge_clients — droit à l'oubli RGPD, purge différée.

Anonymise irréversiblement les clients désactivés (soft delete, cf.
gestion:client_delete) depuis plus de N mois : les champs identifiants
(nom, prenom, email, telephone) sont mis à NULL via l'API existante
(PUT /api/clients/{id}), le compte de connexion Django associé (s'il
existe) est supprimé pour révoquer tout accès.

Ne fait JAMAIS de DELETE physique sur la table clients — conforme au
principe soft-delete du projet (constitution, Principe IV). Les données
non identifiantes (age, sexe, imc, enfants, fumeur, region) restent en
base pour préserver l'historique agrégé (predictions, contrats), une
fois anonymisées elles ne permettent plus d'identifier une personne.

Usage :
    python manage.py purge_clients --months=6
    python manage.py purge_clients --months=6 --dry-run
"""

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from accounts.models import ProfilUtilisateur
from utils import api_client
from utils.api_client import ApiError, ApiTimeoutError, ApiUnavailableError

CHAMPS_IDENTIFIANTS = ["nom", "prenom", "email", "telephone"]


class Command(BaseCommand):
    help = (
        "Anonymise les clients désactivés depuis plus de N mois "
        "(droit à l'oubli RGPD) — jamais de suppression physique."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--months",
            type=int,
            default=6,
            help="Ancienneté minimale de date_suppression, en mois (défaut : 6).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="N'effectue aucune modification, liste les clients concernés.",
        )

    def handle(self, *args, **options):
        months = options["months"]
        dry_run = options["dry_run"]
        seuil = datetime.utcnow() - timedelta(days=months * 30)

        try:
            clients = api_client.get_all_clients(actifs_only=False)
        except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
            self.stderr.write(self.style.ERROR(f"API indisponible : {exc}"))
            return

        a_purger = [
            c
            for c in clients
            if self._date_suppression_ancienne(c, seuil) and not self._deja_anonymise(c)
        ]

        if not a_purger:
            self.stdout.write("Aucun client à purger.")
            return

        self.stdout.write(
            f"{len(a_purger)} client(s) désactivé(s) depuis plus de {months} mois."
        )

        for c in a_purger:
            client_id = c["client_id"]

            if dry_run:
                self.stdout.write(f"  [dry-run] client #{client_id} serait anonymisé")
                continue

            try:
                api_client.update_client(
                    client_id, {champ: None for champ in CHAMPS_IDENTIFIANTS}
                )
            except (ApiUnavailableError, ApiTimeoutError, ApiError) as exc:
                self.stderr.write(
                    self.style.ERROR(
                        f"  Échec anonymisation client #{client_id} : {exc}"
                    )
                )
                continue

            profils = ProfilUtilisateur.objects.filter(client_id=client_id)
            nb_comptes = profils.count()
            for profil in profils:
                profil.user.delete()  # cascade : supprime aussi le ProfilUtilisateur

            suffixe = " (compte de connexion supprimé)" if nb_comptes else ""
            self.stdout.write(
                self.style.SUCCESS(f"  Client #{client_id} anonymisé{suffixe}")
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Mode dry-run : aucune modification effectuée.")
            )

    @staticmethod
    def _date_suppression_ancienne(client: dict, seuil: datetime) -> bool:
        valeur = client.get("date_suppression")
        if not valeur:
            return False
        # L'API renvoie un TIMESTAMP PostgreSQL naïf (pas de fuseau) — on
        # compare donc à une borne naïve (UTC) plutôt qu'à un datetime
        # timezone-aware, pour éviter une comparaison incompatible.
        date_supp = datetime.fromisoformat(valeur).replace(tzinfo=None)
        return date_supp < seuil

    @staticmethod
    def _deja_anonymise(client: dict) -> bool:
        """Idempotence : un client déjà purgé n'a plus aucun champ identifiant."""
        return not any(client.get(champ) for champ in CHAMPS_IDENTIFIANTS)
