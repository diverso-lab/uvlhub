"""E9: what 3.0 makes from its data, made again by the features' own
commands in processes of their own (DM-6), and a run it never stops.

The rehearsal runs factlabel's and uvl's commands as the cutover does. Its
reindex runs with ELASTICSEARCH_ENABLED=false (conftest), since the
development's search node is shared: it fails, as it would without a node,
and that is an alert.
"""

from __future__ import annotations

import sqlalchemy as sa

from splent_io.splent_feature_factlabel.metrics_extraction import EXTRACTOR_VERSION


def rows(migrated, sql):
    with migrated.engine.connect() as connection:
        return [dict(row) for row in connection.execute(sa.text(sql)).mappings()]


def test_e9_computes_every_factlabel_and_the_metrics_from_it(migrated):
    schema = migrated.params.target_schema
    commands = migrated.report["facts"]["derived"]["commands"]
    assert commands["factlabel"]["ok"] is True
    stored = {
        r["id"]
        for r in rows(
            migrated, f"SELECT id FROM `{schema}`.hubfiles WHERE storage_status = 'ok'"
        )
    }
    labelled = {
        r["hubfile_id"]
        for r in rows(
            migrated,
            f"SELECT hubfile_id FROM `{schema}`.hubfile_factlabel "
            "WHERE factlabel_json <> ''",
        )
    }
    assert stored <= labelled
    # v2.12's metrics of hubfile 1 (extractor 1.0) are made again from its
    # FactLabel (§7.3).
    metrics = rows(
        migrated,
        f"SELECT hubfile_id, extractor_version FROM `{schema}`.hubfile_metrics",
    )
    versions = {m["hubfile_id"]: m["extractor_version"] for m in metrics}
    assert versions[1] == EXTRACTOR_VERSION != "1.0"
    assert set(versions) >= stored


def test_e9_makes_the_formats_of_every_uvl_model(migrated):
    commands = migrated.report["facts"]["derived"]["commands"]
    assert commands["formats"]["ok"] is True
    derived = migrated.params.store_root / "datasets" / "1" / "derived" / "1"
    assert derived.is_dir() and any(derived.iterdir())
    assert migrated.report["facts"]["derived"]["made"]["format_files"] > 0


def test_a_reindex_that_fails_is_an_alert_and_stops_nothing(migrated):
    report = migrated.report
    assert report["stopped"] is None
    checks = {c["name"]: c for c in report["checks"]}
    assert not checks["E9-reindex"]["ok"] and not checks["E9-reindex"]["blocking"]
    assert checks["E9-factlabel"]["ok"] and checks["E9-formats"]["ok"]
    assert len(report["alerts"]) == 1
    assert report["alerts"][0].startswith("E9 reindex: env ELASTICSEARCH_ENABLED=false")
    assert "SQL fallback" in report["alerts"][0]
