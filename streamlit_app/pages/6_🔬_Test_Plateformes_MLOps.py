"""
Module 6 — Test plateformes MLOps.

Preuve de concept : comparaison mesurée entre MLflow (retenu) et
Weights & Biases (écarté au benchmark sur la contrainte de localité).

La page ne fait aucun appel réseau : elle lit les deux exports JSON produits
par `python -m poc.train_double`.
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Test plateformes MLOps — AssuML", page_icon="🔬", layout="wide"
)
st.title("🔬 Test plateformes MLOps — MLflow contre Weights & Biases")

DOSSIER_POC = Path(__file__).resolve().parents[2] / "poc"
EXPORT_MLFLOW = DOSSIER_POC / "export_mlflow.json"
EXPORT_WANDB = DOSSIER_POC / "export_wandb.json"


def charger(chemin: Path):
    """Lit un export JSON, ou None s'il n'existe pas encore."""
    if not chemin.exists():
        return None
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


st.markdown(
    """
    Le benchmark de veille (C7) affirmait, sur la seule foi de la documentation
    éditeur, que Weights & Biases offrait *« une expérience de comparaison
    supérieure »* à MLflow. Cette preuve de concept remplace cette affirmation
    par une mesure : **un seul entraînement, journalisé dans les deux backends**.
    """
)

mlf = charger(EXPORT_MLFLOW)
wb = charger(EXPORT_WANDB)

if mlf is None:
    st.warning("Aucun export trouvé. Lancez d'abord l'expérience :", icon="⚠️")
    st.code(
        "pip install -r poc/requirements-poc.txt\n"
        "wandb login\n"
        "python -m poc.train_double",
        language="bash",
    )
    st.caption(
        "Sans compte W&B : `python -m poc.train_double --sans-wandb` "
        "(la page affichera la colonne MLflow seule)."
    )
    st.stop()

# ── 1. Le témoin ──────────────────────────────────────────────────────────────

st.divider()
st.subheader("1. Le témoin — les métriques doivent être identiques")
st.caption(
    "Même jeu, même graine, même exécution. Des chiffres identiques prouvent que "
    "les deux intégrations enregistrent correctement. Ce n'est pas le résultat "
    "du POC : c'est ce qui le valide."
)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"**{mlf['outil']}** · version {mlf['version']}")
    for cle, valeur in mlf["metriques"].items():
        st.metric(
            cle.upper(), f"{valeur:.4f}" if abs(valeur) < 10 else f"{valeur:,.2f}"
        )
with col_b:
    if wb is None:
        st.info("Export W&B absent — expérience lancée avec `--sans-wandb`.")
    else:
        st.markdown(f"**{wb['outil']}** · version {wb['version']}")
        for cle, valeur in wb["metriques"].items():
            st.metric(
                cle.upper(), f"{valeur:.4f}" if abs(valeur) < 10 else f"{valeur:,.2f}"
            )

if wb is not None:
    if mlf["metriques"] == wb["metriques"]:
        st.success(
            "Témoin validé : les deux backends ont enregistré exactement les mêmes "
            "métriques pour le même entraînement.",
            icon="✅",
        )
    else:
        st.error(
            "Écart entre les deux enregistrements — l'une des intégrations est "
            "fautive, la comparaison qui suit n'est pas exploitable.",
            icon="⚠️",
        )

# ── 2. Grille comparative ─────────────────────────────────────────────────────

st.divider()
st.subheader("2. Ce que le POC compare réellement")
st.caption(
    "Trois niveaux de preuve, explicitement distingués : ce qui est mesuré, "
    "ce qui est constaté, et ce qui relève du jugement."
)


def valeur(source, cle, defaut="—"):
    """Lit une clé d'un export, avec repli si l'export est absent."""
    if source is None:
        return "—"
    v = source.get(cle, defaut)
    if isinstance(v, bool):
        return "oui" if v else "non"
    return v


st.markdown("##### Mesuré")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Critère": "Lignes d'intégration dans le script",
                "MLflow": valeur(mlf, "lignes_integration"),
                "Weights & Biases": valeur(wb, "lignes_integration"),
            },
            {
                "Critère": "Taille installée (Mo)",
                "MLflow": valeur(mlf, "taille_installee_mo"),
                "Weights & Biases": valeur(wb, "taille_installee_mo"),
            },
            {
                "Critère": "Dépendances directes",
                "MLflow": valeur(mlf, "dependances_directes"),
                "Weights & Biases": valeur(wb, "dependances_directes"),
            },
            {
                "Critère": "Surcoût de journalisation (s)",
                "MLflow": valeur(mlf, "surcout_journalisation_s"),
                "Weights & Biases": valeur(wb, "surcout_journalisation_s"),
            },
            {
                "Critère": "Fonctionne sans réseau",
                "MLflow": valeur(mlf, "hors_ligne"),
                "Weights & Biases": valeur(wb, "hors_ligne"),
            },
        ]
    ),
    hide_index=True,
    use_container_width=True,
)

st.markdown("##### Constaté")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Critère": "Compte requis",
                "MLflow": valeur(mlf, "compte_requis"),
                "Weights & Biases": valeur(wb, "compte_requis"),
            },
            {
                "Critère": "Où résident les données",
                "MLflow": valeur(mlf, "donnees_residentes"),
                "Weights & Biases": valeur(wb, "donnees_residentes"),
            },
            {
                "Critère": "Sortie du périmètre local",
                "MLflow": valeur(mlf, "sortie_du_perimetre_local"),
                "Weights & Biases": valeur(wb, "sortie_du_perimetre_local"),
            },
        ]
    ),
    hide_index=True,
    use_container_width=True,
)

st.markdown("##### Apprécié")
st.info(
    "L'ergonomie de comparaison entre exécutions — l'argument central du "
    "benchmark — reste un jugement. Le POC ne peut pas la mesurer, et le dire "
    "fait partie de sa conclusion.",
    icon="ℹ️",
)

# ── 3. Conclusion ─────────────────────────────────────────────────────────────

st.divider()
st.subheader("3. Conclusion — avis pour la poursuite du projet")
st.markdown(
    """
    **Aucun défaut fonctionnel n'a été constaté sur Weights & Biases.** Les deux
    outils enregistrent les mêmes métriques pour le même entraînement, et
    l'intégration se fait dans les deux cas en quelques appels.

    La recommandation du benchmark est **maintenue, mais pour un motif désormais
    éprouvé plutôt que documentaire** : W&B suppose un compte et fait sortir les
    métriques du périmètre local, ce que la contrainte du projet interdit.
    MLflow s'exécute contre un fichier SQLite, sans serveur ni compte.

    Ce que le POC change dans le rapport E2 : la formulation
    *« adapté fonctionnellement, écarté sur les contraintes »* devient
    *« testé en preuve de concept, écarté sur la contrainte de localité —
    sans défaut fonctionnel constaté »*.
    """
)

horodatage = mlf.get("exporte_le", "inconnu")
st.caption(
    f"Exports lus depuis `poc/` — expérience réalisée le {horodatage}. "
    "La page ne joint aucun service distant : elle relit des fichiers figés, "
    "ce qui la rend reproductible et indépendante du réseau."
)
