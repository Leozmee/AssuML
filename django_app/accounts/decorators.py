"""Décorateurs d'autorisation pour les vues AssuML."""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def admin_required(view_func):
    """Exige que l'utilisateur soit connecté ET ait le rôle 'admin'."""

    @wraps(view_func)
    @login_required(login_url="/accounts/login/")
    def wrapper(request, *args, **kwargs):
        try:
            if request.user.profil.role == "admin":
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        return redirect("/accounts/login/")

    return wrapper
