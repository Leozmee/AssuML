"""Configuration pytest-django pour les tests AssuML."""

import pytest

from accounts.models import ProfilUtilisateur, User


@pytest.fixture
def admin_user(db):
    """Utilisateur admin avec ProfilUtilisateur."""
    user = User.objects.create_user(email="admin_test@assuml.fr", password="pwd123")
    ProfilUtilisateur.objects.create(user=user, role="admin")
    return user


@pytest.fixture
def client_user(db):
    """Utilisateur assuré avec ProfilUtilisateur et client_id fictif."""
    user = User.objects.create_user(email="user_test@assuml.fr", password="pwd123")
    ProfilUtilisateur.objects.create(user=user, role="user", client_id=42)
    return user


@pytest.fixture
def admin_client(client, admin_user):
    """Client de test connecté en admin."""
    client.force_login(admin_user)
    return client


@pytest.fixture
def user_client(client, client_user):
    """Client de test connecté en user."""
    client.force_login(client_user)
    return client
