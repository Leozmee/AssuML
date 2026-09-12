"""
Barrière de non-régression pour l'intégration continue — AssuML.

Pourquoi ce script existe :
    Le garde-fou de mlflow_gate.py s'exécute pendant l'entraînement et refuse
    de remplacer un .pkl par un modèle moins performant. Mais il compare à la
    métrique du modèle physiquement déployé : sur un checkout neuf, aucun .pkl
    n'existe (ils sont gitignorés), la référence vaut None et le premier
    entraînement passe sans contrôle (cf. lire_metrique_actuelle, paramètre
    model_path — sans quoi aucun modèle ne serait jamais déployable).

    Le garde-fou ne protège donc que la machine de développement. Une recette
    dégradée — hyperparamètres, graine, features, jeu de données — commitée
    sans entraînement local traverserait la CI puis le déploiement sans
    rencontrer d'obstacle. Il ne bloque d'ailleurs rien même en local : il
    avertit, puis le script sort en code 0.

Ce que fait ce script :
    Il compare les métriques que l'entraînement vient d'écrire dans
    metadata.json à celles de la version COMMITÉE du même fichier, lue via
    `git show`. Si l'une des deux a régressé au-delà de la tolérance, il sort
    en code 1 et fait échouer le job.

    La comparaison porte sur les mêmes métriques que le garde-fou :
    r2 pour la régression, f1_macro pour la classification.

Usage :
    python -m ml_models.training.verifier_non_regression
    python -m ml_models.training.verifier_non_regression --tolerance 0.002
"""

import argparse
import json
import subprocess
import sys

CHEMIN_METADATA = "ml_models/saved_models/metadata.json"

# Métrique de référence par modèle — identique à celle du garde-fou
# (cf. train_regression.py et train_classification.py). Toutes deux sont
# "plus grand = meilleur".
METRIQUES = {
    "regression": "r2",
    "classification": "f1_macro",
}

# Marge absorbant les écarts de dernière décimale entre plateformes
# (entraînement local macOS vs runner Ubuntu). Une vraie régression se
# compte en centièmes, très au-delà de cette marge.
TOLERANCE_DEFAUT = 0.001


def lire_reference_committee(chemin: str = CHEMIN_METADATA) -> dict | None:
    """Lit la version committée de metadata.json, sans toucher au disque.

    L'entraînement réécrit metadata.json : la référence doit donc être lue
    dans Git, pas dans le fichier de travail, qui contient déjà les nouvelles
    valeurs au moment où ce script s'exécute.

    Args:
        chemin: Chemin du fichier, relatif à la racine du dépôt.

    Returns:
        dict | None: Le contenu committé, ou None si Git est indisponible ou
        si le fichier n'est pas encore suivi (premier commit).
    """
    try:
        sortie = subprocess.run(
            ["git", "show", f"HEAD:{chemin}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(sortie.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        return None


def lire_metriques(meta: dict, cle_modele: str) -> dict:
    """Extrait le bloc metriques_test d'un modèle, quel que soit le format.

    Gère l'ancien format plat (régression à la racine) autant que le format
    imbriqué actuel.

    Args:
        meta: Contenu de metadata.json.
        cle_modele: "regression" ou "classification".

    Returns:
        dict: Les métriques de test, ou un dict vide si le bloc est absent.
    """
    bloc = meta.get(cle_modele)
    if bloc is None and cle_modele == "regression" and "algorithme" in meta:
        bloc = meta  # ancien format plat
    if not isinstance(bloc, dict):
        return {}
    return bloc.get("metriques_test", {})


def comparer(reference: dict, courant: dict, tolerance: float) -> list[str]:
    """Compare les métriques courantes à la référence committée.

    Args:
        reference: metadata.json tel que committé.
        courant: metadata.json tel que réécrit par l'entraînement.
        tolerance: Écart négatif toléré avant de considérer une régression.

    Returns:
        list[str]: Un message par régression détectée, vide si tout va bien.
    """
    regressions = []
    for cle_modele, cle_metrique in METRIQUES.items():
        attendu = lire_metriques(reference, cle_modele).get(cle_metrique)
        obtenu = lire_metriques(courant, cle_modele).get(cle_metrique)

        if attendu is None or obtenu is None:
            print(f"  {cle_modele:<15} {cle_metrique} absent — comparaison ignorée")
            continue

        ecart = obtenu - attendu
        if ecart < -tolerance:
            regressions.append(
                f"{cle_modele} : {cle_metrique}={obtenu:.4f} contre "
                f"{attendu:.4f} attendu (écart {ecart:+.4f})"
            )
            etat = "RÉGRESSION"
        else:
            etat = "OK"
        print(
            f"  {cle_modele:<15} {cle_metrique}={obtenu:.4f} "
            f"(référence {attendu:.4f}, écart {ecart:+.4f}) — {etat}"
        )
    return regressions


def main() -> int:
    """Point d'entrée — retourne le code de sortie du processus."""
    parser = argparse.ArgumentParser(
        description=(
            "Vérifie qu'aucun modèle n'a régressé face à la référence committée."
        )
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=TOLERANCE_DEFAUT,
        help=f"Écart négatif toléré (défaut : {TOLERANCE_DEFAUT}).",
    )
    args = parser.parse_args()

    print("Vérification de non-régression des modèles")
    print("=" * 55)

    reference = lire_reference_committee()
    if reference is None:
        print("  Aucune référence committée — vérification ignorée.")
        return 0

    try:
        with open(CHEMIN_METADATA, encoding="utf-8") as f:
            courant = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"  metadata.json illisible : {exc}", file=sys.stderr)
        return 1

    regressions = comparer(reference, courant, args.tolerance)
    print("=" * 55)

    if regressions:
        print(
            "\nRégression détectée — la recette committée produit un modèle "
            "moins performant que celui annoncé dans metadata.json :\n",
            file=sys.stderr,
        )
        for ligne in regressions:
            print(f"  - {ligne}", file=sys.stderr)
        print(
            "\nRelancer l'entraînement en local, vérifier le changement de recette,"
            "\net committer le metadata.json correspondant si la baisse est assumée.",
            file=sys.stderr,
        )
        return 1

    print("Aucune régression.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
