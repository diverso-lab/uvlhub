"""Persist extracted metrics into the `hubfile_metrics` table.

Lives in its own module (rather than alongside the pure extractor) because
this side touches the DB and the Flask session: the extractor stays import-
safe for tests and CLI tools that don't want a DB connection.

The upsert is "last write wins" per `hubfile_id`. A row is always written —
even when extraction fails — with `parse_error` set, so the dashboard can
report coverage as `COUNT(parse_error IS NULL) / COUNT(*)`.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Mapping

import pytz

from app import db
from app.modules.hubfile.metrics_extraction import extract_metrics
from app.modules.hubfile.models import HubfileMetrics

logger = logging.getLogger(__name__)


def upsert_metrics_from_payload(hubfile_id: int, factlabel_json: str | Mapping[str, Any] | None) -> HubfileMetrics:
    """Extract metrics from a payload and upsert the row for `hubfile_id`.

    The caller owns the surrounding session/commit semantics: this function
    flushes through SQLAlchemy but does not commit, so it can participate
    in a wider transaction (e.g. inside `compute_factlabel`, where the
    fact label commit has already happened — we commit here too to keep
    the metrics row in sync).
    """
    fields = extract_metrics(factlabel_json)

    row = db.session.get(HubfileMetrics, hubfile_id)
    if row is None:
        row = HubfileMetrics(hubfile_id=hubfile_id)
        db.session.add(row)

    row.extracted_at = datetime.now(pytz.utc)
    for column, value in fields.items():
        setattr(row, column, value)

    db.session.commit()
    return row
