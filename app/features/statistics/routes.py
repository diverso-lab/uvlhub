import csv
import io
import json
from dataclasses import asdict
from datetime import datetime

from flask import Response, render_template, stream_with_context

from app.features.statistics import statistics_bp
from app.features.statistics.services import CorpusExportService, DashboardService


def _charts_payload(dashboard) -> dict:
    """Flatten the pieces the client needs for Chart.js into a plain dict.

    Rendered inside a `<script type="application/json">` block; keeping the
    conversion in Python (rather than Jinja) avoids having to reach for
    `__dict__`/`asdict` filter hacks and makes the shape explicit.
    """
    corpus = dashboard.corpus
    return {
        "months": dashboard.months,
        "uploads": dashboard.uploads_per_month,
        "views": dashboard.views_per_month,
        "downloads": dashboard.downloads_per_month,
        "satisfiability": {
            "yes": corpus.satisfiable_count,
            "no": corpus.unsatisfiable_count,
            "unknown": corpus.unknown_satisfiability,
        },
        "featuresHistogram": [asdict(b) for b in corpus.features_histogram],
        "constraintsHistogram": [asdict(b) for b in corpus.constraints_histogram],
        "depthHistogram": [asdict(b) for b in corpus.depth_histogram],
        "configurationsHistogram": [asdict(b) for b in corpus.configurations_histogram],
        "constraintTypes": [list(t) for t in corpus.constraint_types],
        "groupTypes": [list(t) for t in corpus.group_types],
    }


@statistics_bp.route("/statistics", methods=["GET"])
def index():
    dashboard = DashboardService().build_dashboard()
    return render_template(
        "statistics/index.html",
        dashboard=dashboard,
        charts_payload=_charts_payload(dashboard),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Reproducibility exports
#
# A frozen-in-time snapshot of the corpus metrics — one row per hubfile, every
# numeric column on `hubfile_metrics`, plus enough dataset metadata to cite each
# row. The DB access lives in CorpusExportService; the routes only stream it.
# ─────────────────────────────────────────────────────────────────────────────


@statistics_bp.route("/statistics/export.csv", methods=["GET"])
def export_csv():
    export_service = CorpusExportService()
    columns = export_service.export_columns()

    def generate():
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=columns)
        writer.writeheader()
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)

        for row in export_service.iter_rows():
            writer.writerow(row)
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    filename = f"uvlhub-corpus-metrics-{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return Response(
        stream_with_context(generate()),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@statistics_bp.route("/statistics/export.json", methods=["GET"])
def export_json():
    export_service = CorpusExportService()

    def generate():
        yield "["
        first = True
        for row in export_service.iter_rows():
            prefix = "" if first else ","
            yield prefix + json.dumps(row, default=str)
            first = False
        yield "]"

    filename = f"uvlhub-corpus-metrics-{datetime.utcnow().strftime('%Y%m%d')}.json"
    return Response(
        stream_with_context(generate()),
        mimetype="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
