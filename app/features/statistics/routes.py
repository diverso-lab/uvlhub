import csv
import io
import json
from dataclasses import asdict
from datetime import datetime

from flask import Response, render_template, stream_with_context

from app import db
from app.features.statistics import statistics_bp
from app.features.statistics.services import DashboardService


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
# These hand the paper a frozen-in-time snapshot of the corpus metrics — one
# row per hubfile, every numeric column on `hubfile_metrics`, plus enough
# dataset metadata to cite each row. Generating tables/figures from the
# downloaded file (rather than from the live dashboard) keeps the paper
# reproducible even after the corpus grows.
# ─────────────────────────────────────────────────────────────────────────────


def _export_columns() -> list[str]:
    """Columns to include in CSV/JSON exports, in display order."""
    from app.features.hubfile.models import HubfileMetrics

    skip = {"hubfile_id", "extracted_at", "extractor_version", "parse_error"}
    metric_cols = [c.name for c in HubfileMetrics.__table__.columns if c.name not in skip]
    return [
        "hubfile_id",
        "hubfile_name",
        "dataset_id",
        "dataset_title",
        "dataset_doi",
        "extracted_at",
        "extractor_version",
        "parse_error",
        *metric_cols,
    ]


def _iter_export_rows():
    """Yield one dict per hubfile that has a metrics row.

    Streamed instead of materialised so a 50k-hubfile export doesn't blow
    up memory (and so the user gets the first bytes immediately).
    """
    from app.features.dataset.models import DataSet, DSMetaData
    from app.features.featuremodel.models import FeatureModel
    from app.features.hubfile.models import Hubfile, HubfileMetrics

    columns = _export_columns()
    metric_cols = [
        c
        for c in columns
        if c
        not in {
            "hubfile_id",
            "hubfile_name",
            "dataset_id",
            "dataset_title",
            "dataset_doi",
            "extracted_at",
            "extractor_version",
            "parse_error",
        }
    ]

    q = (
        db.session.query(HubfileMetrics, Hubfile, DataSet, DSMetaData)
        .join(Hubfile, Hubfile.id == HubfileMetrics.hubfile_id)
        .join(FeatureModel, FeatureModel.id == Hubfile.feature_model_id)
        .join(DataSet, DataSet.id == FeatureModel.dataset_id)
        .join(DSMetaData, DSMetaData.id == DataSet.ds_meta_data_id)
        .order_by(HubfileMetrics.hubfile_id)
    )

    for metrics, hubfile, dataset, meta in q.yield_per(500):
        row = {
            "hubfile_id": metrics.hubfile_id,
            "hubfile_name": hubfile.name,
            "dataset_id": dataset.id,
            "dataset_title": meta.title,
            "dataset_doi": meta.dataset_doi,
            "extracted_at": metrics.extracted_at.isoformat() if metrics.extracted_at else None,
            "extractor_version": metrics.extractor_version,
            "parse_error": metrics.parse_error,
        }
        for col in metric_cols:
            row[col] = getattr(metrics, col)
        yield row


@statistics_bp.route("/statistics/export.csv", methods=["GET"])
def export_csv():
    columns = _export_columns()

    def generate():
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=columns)
        writer.writeheader()
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)

        for row in _iter_export_rows():
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
    def generate():
        yield "["
        first = True
        for row in _iter_export_rows():
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
