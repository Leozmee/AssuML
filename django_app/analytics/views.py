"""Vue analytics Big Data — admin uniquement."""

import json
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render

from accounts.decorators import admin_required
from utils import api_client, region_id_to_nom
from utils.api_client import ApiError, ApiTimeoutError, ApiUnavailableError

PARQUET_PATH = Path(settings.REPO_ROOT) / "data" / "big_data" / "insurance_big.parquet"


@admin_required
def dashboard(request):
    """Dashboard analytique — KPIs et graphiques 100% depuis DuckDB/Parquet."""
    kpis = {}
    charts = {}
    contexte_regional = []

    try:
        from big_data.duckdb_analytics import DuckDBAnalytics

        if not PARQUET_PATH.exists():
            raise FileNotFoundError(f"Fichier Parquet absent : {PARQUET_PATH}")

        analytics = DuckDBAnalytics(str(PARQUET_PATH))

        def _to_json(df, x_col, y_col, chart_type="bar"):
            if df is None or df.empty:
                return "[]"
            x_vals = [str(v) if isinstance(v, bool) else v for v in df[x_col].tolist()]
            return json.dumps(
                [{"type": chart_type, "x": x_vals, "y": df[y_col].tolist()}]
            )

        def _to_table(df, x_col, y_col, x_label, y_label):
            """Alternative textuelle d'un graphique Plotly (mêmes données tracées)."""
            if df is None or df.empty:
                return []
            x_vals = [str(v) if isinstance(v, bool) else v for v in df[x_col].tolist()]
            return [
                {x_label: x, y_label: y} for x, y in zip(x_vals, df[y_col].tolist())
            ]

        tables = {}

        df_region = analytics.stats_par_region()
        charts["par_region"] = _to_json(df_region, "region", "cout_moy")
        tables["par_region"] = _to_table(
            df_region, "region", "cout_moy", "Région", "Coût moyen prédit ($)"
        )

        df_fumeur = analytics.stats_par_fumeur()
        if df_fumeur is not None and not df_fumeur.empty:
            df_fumeur = df_fumeur.copy()
            df_fumeur["fumeur"] = df_fumeur["fumeur"].map(
                {True: "Fumeur", False: "Non-fumeur"}
            )
        charts["par_fumeur"] = _to_json(df_fumeur, "fumeur", "cout_moy")
        tables["par_fumeur"] = _to_table(
            df_fumeur, "fumeur", "cout_moy", "Statut fumeur", "Coût moyen prédit ($)"
        )

        dist = analytics.distribution_cout()
        if dist is not None and not dist.empty:
            dist = dist.copy()
            dist["label"] = dist["bin_min"].apply(lambda x: f"{x // 1000}k$")
            charts["distribution"] = _to_json(dist, "label", "nb")
        else:
            charts["distribution"] = "[]"
        tables["distribution"] = _to_table(
            dist, "label", "nb", "Tranche de coût prédit ($)", "Nombre de profils"
        )

        df_corr = analytics.correlation_age_cout()
        charts["correlation"] = _to_json(df_corr, "age", "cout_moy")
        tables["correlation"] = _to_table(
            df_corr, "age", "cout_moy", "Âge", "Coût moyen prédit ($)"
        )

        df_imc_region = analytics.imc_moyen_par_region()
        charts["imc_region"] = _to_json(df_imc_region, "region", "imc_moy")
        tables["imc_region"] = _to_table(
            df_imc_region, "region", "imc_moy", "Région", "IMC moyen"
        )

        df_fumeurs_region = analytics.effectif_fumeurs_par_region()
        charts["fumeurs_region"] = _to_json(df_fumeurs_region, "region", "nb_fumeurs")
        tables["fumeurs_region"] = _to_table(
            df_fumeurs_region, "region", "nb_fumeurs", "Région", "Nombre de fumeurs"
        )

        layouts = {
            "par_region": json.dumps(
                {
                    "xaxis": {"title": "Région"},
                    "yaxis": {"title": "Coût moyen prédit ($)"},
                }
            ),
            "par_fumeur": json.dumps(
                {
                    "xaxis": {"title": "Statut fumeur"},
                    "yaxis": {"title": "Coût moyen prédit ($)"},
                }
            ),
            "distribution": json.dumps(
                {
                    "xaxis": {"title": "Tranche de coût prédit ($, pas de 5 000)"},
                    "yaxis": {"title": "Nombre de profils"},
                }
            ),
            "correlation": json.dumps(
                {
                    "xaxis": {"title": "Âge"},
                    "yaxis": {"title": "Coût moyen prédit ($)"},
                }
            ),
            "imc_region": json.dumps(
                {
                    "xaxis": {"title": "Région"},
                    "yaxis": {"title": "IMC moyen"},
                }
            ),
            "fumeurs_region": json.dumps(
                {
                    "xaxis": {"title": "Région"},
                    "yaxis": {"title": "Nombre de fumeurs"},
                }
            ),
        }
        profils = analytics.top_profils_risque()
        charts["profils"] = (
            profils.to_dict(orient="records")
            if profils is not None and not profils.empty
            else []
        )

        globales = analytics.stats_globales()
        if globales is not None and not globales.empty:
            g = globales.iloc[0]
            kpis = {
                "nb_clients": int(g["nb_total"]),
                "cout_moyen": round(float(g["cout_moy"]), 2),
                "taux_fumeurs": round(float(g["pct_fumeurs"]), 1),
                "age_moyen": round(float(g["age_moy"]), 1),
            }

        # Contexte régional : Big Data + météo (API) + statistiques de
        # santé régionales (BDD externe) — dans son propre try/except pour
        # qu'une source externe manquante (météo/stats non encore chargées)
        # ne désactive pas le reste du tableau de bord.
        try:
            meteo = api_client.get_meteo() or []
            stats = api_client.get_stats_regionales() or []
            if meteo and stats:
                df_meteo = pd.DataFrame(meteo)
                df_meteo["nom_region"] = df_meteo["region_id"].apply(region_id_to_nom)
                df_stats = pd.DataFrame(stats)
                df_stats["nom_region"] = df_stats["region_id"].apply(region_id_to_nom)
                contexte_regional = analytics.contexte_regional(
                    df_meteo, df_stats
                ).to_dict(orient="records")
        except (ApiUnavailableError, ApiTimeoutError, ApiError):
            contexte_regional = []

    except Exception as exc:
        messages.warning(request, f"Analytics DuckDB indisponibles : {exc}")
        charts = {}
        layouts = {}
        tables = {}
        contexte_regional = []

    return render(
        request,
        "analytics/dashboard.html",
        {
            "kpis": kpis,
            "charts": charts,
            "layouts": layouts,
            "tables": tables,
            "contexte_regional": contexte_regional,
        },
    )
