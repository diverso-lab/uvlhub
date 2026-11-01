"""The report: what a run leaves to read once the server is gone."""

from __future__ import annotations

import sqlalchemy as sa


def work(migrated, table):
    with migrated.engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                sa.text(f"SELECT * FROM `{migrated.params.work_schema}`.`{table}`")
            ).mappings()
        ]


def test_the_report_details_every_conflict_but_what_is_personal(migrated):
    """The report says what each conflict is about, so it can be read once
    the server is gone; of the accounts', only the rows."""
    detail = migrated.report["conflict_detail"]
    assert len(detail) == len(work(migrated, "conflict"))
    by_kind = {}
    for conflict in detail:
        by_kind.setdefault(conflict["kind"], []).append(conflict)
    (sandbox,) = by_kind["doi_not_zenodo"]
    assert sandbox == {
        "kind": "doi_not_zenodo",
        "entity": "ds_meta_data",
        "ref": "10.5072/zenodo.55",
        "source_rows": ["ds_meta_data:208"],
        "detail": "not a DOI of Zenodo's production (10.5281)",
        "status": "open",
    }
    accounts = [
        c
        for kind, cs in by_kind.items()
        for c in cs
        if kind.startswith(("email_", "identity_"))
    ]
    assert accounts and all(
        c["ref"] is None and c["detail"] is None and c["source_rows"] for c in accounts
    )
