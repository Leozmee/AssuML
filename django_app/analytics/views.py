"""Vue analytics Big Data — admin uniquement."""

import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render

from accounts.decorators import admin_required

PARQUET_PATH = Path(settings.REPO_ROOT) / "data" / "big_data" / "insurance_big.parquet"


@admin_required
def dashboard(request):
    """Dashboard analytique — KPIs et graphiques 100% depuis DuckDB/Parquet."""
    kpis = {}
    charts = {}

    try:
        from big_data.duckdb_analytics import DuckDBAnalytics

        if not PARQUET_PATH.exists():
            raise FileNotFoundError(f"Fichier Parquet absent : {PARQUET_PATH}")

        analytics = DuckDBAnalytics(str(PARQUET_PATH))

        def _to_json(df):
            if df is None or df.empty:
                return "[]"
            x_vals = [
                str(v) if isinstance(v, bool) else v for v in df.iloc[:, 0].tolist()
            ]
            return json.dumps(
                [{"type": "bar", "x": x_vals, "y": df.iloc[:, 1].tolist()}]
            )

        charts["par_region"] = _to_json(analytics.stats_par_region())
        charts["par_fumeur"] = _to_json(analytics.stats_par_fumeur())
        dist = analytics.distribution_cout()
        charts["distribution"] = json.dumps(
            [{"type": "histogram", "x": dist.iloc[:, 0].tolist()}]
            if dist is not None and not dist.empty
            else []
        )
        charts["correlation"] = _to_json(analytics.correlation_age_cout())
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

    except Exception as exc:
        messages.warning(request, f"Analytics DuckDB indisponibles : {exc}")
        charts = {}

    return render(
        request,
        "analytics/dashboard.html",
        {"kpis": kpis, "charts": charts},
    )
