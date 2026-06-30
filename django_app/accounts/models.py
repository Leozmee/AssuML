"""Modèles d'authentification AssuML — double rôle admin/user."""

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    """Manager custom : utilise email comme identifiant unique, pas username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Utilisateur AssuML — identifié par email (pas de username)."""

    objects = UserManager()

    username = None
    email = models.EmailField(unique=True, verbose_name="Adresse email")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return self.email


class ProfilUtilisateur(models.Model):
    """Profil étendu — rôle et lien vers le client PostgreSQL."""

    ROLES = [("admin", "Assureur"), ("user", "Assuré")]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profil",
    )
    role = models.CharField(max_length=10, choices=ROLES)
    # NULL pour les admins, ID client PostgreSQL pour les assurés
    client_id = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

    def __str__(self):
        return f"{self.user.email} ({self.role})"

    @property
    def est_admin(self):
        """Retourne True si l'utilisateur est un assureur."""
        return self.role == "admin"
