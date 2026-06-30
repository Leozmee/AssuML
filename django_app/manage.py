#!/usr/bin/env python
"""Point d'entrée Django pour les commandes d'administration."""
import os
import sys


def main():
    """Lance les commandes d'administration Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django introuvable. Vérifiez que le venv est activé."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
