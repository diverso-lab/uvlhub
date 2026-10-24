"""E6: the daily aggregates of use (DM-5), the legacy URLs (CO-2, C-20) and
the notices held until RB-2 ends (D13 b, §5.5), read back from the
rehearsal; and the rules of E5 and E6 that need no database.

synthetic.py says who is who.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime

import pytest
import sqlalchemy as sa

from uvlhub_splent.migration_v2 import rules
from uvlhub_splent.migration_v2.legacy import follow_mappings

from . import synthetic


def rows(migrated, sql):
    with migrated.engine.connect() as connection:
        return [dict(row) for row in connection.execute(sa.text(sql)).mappings()]


def work(migrated, table, order="1"):
    return rows(
        migrated,
        f"SELECT * FROM `{migrated.params.work_schema}`.`{table}` ORDER BY {order}",
    )


def test_e6_aggregates_the_use_of_what_is_published_by_day(migrated):
    usage = [
        (
            r["target_type"],
            r["target_id"],
            r["kind"],
            r["day"],
            r["visitors"],
            r["records"],
        )
        for r in work(migrated, "usage_daily", "target_type, target_id, kind, day")
    ]
    assert usage == [
        # Records 1 and 6 are one browser, 7 is bob: two visitors, three records.
        ("dataset", 1, "view", date(2026, 11, 17), 2, 3),
        ("dataset", 1, "view", date(2026, 11, 18), 1, 1),
        ("hubfile", 1, "download", date(2026, 11, 19), 1, 1),
    ]
    assert {r["source"] for r in work(migrated, "usage_daily")} == {"legacy_v2"}
    counts = {c["entity"]: c for c in work(migrated, "counts")}
    views = counts["ds_view_record"]
    assert (views["source"], views["target"]) == (7, 4)
    assert json.loads(views["detail"]) == {
        "days": 2,
        "no_date": 0,
        "no_target": 0,
        "not_loaded": 1,  # the seed's dataset
        "not_published": 1,  # a draft
        "owner": 1,
    }
    assert json.loads(counts["ds_download_record"]["detail"])["no_target"] == 1
    assert json.loads(counts["hubfile_view_record"]["detail"])["no_date"] == 1
    assert counts["hubfile_download_record"]["target"] == 1


def test_e6_sets_what_v2_12_showed_next_to_what_its_records_give(migrated):
    dm5 = migrated.report["dm5"]
    assert dm5["v2_12_counters"][0]["datasets_viewed"] == 10
    assert dm5["aggregated"]["dataset_views"] == {"visitors": 3, "records": 4}
    assert "showed 10 views and 3 downloads of datasets" in dm5["note"]
    assert "its records give 3 daily visitors" in dm5["note"]


def test_e6_follows_the_doi_mappings_and_keeps_the_legacy_urls(migrated):
    schema = migrated.params.target_schema
    mapped = rows(
        migrated,
        f"SELECT id, dataset_doi_old, dataset_doi_new FROM `{schema}`.doi_mapping ORDER BY id",
    )
    assert [(m["id"], m["dataset_doi_old"], m["dataset_doi_new"]) for m in mapped] == [
        (1, "10.5281/zenodo.999", "10.5281/zenodo.1001"),
        # 998 led to 999: it goes to where 999 goes, in one hop.
        (2, "10.5281/zenodo.998", "10.5281/zenodo.1001"),
    ]
    dropped = {
        r["ref_id"]: r["reason"]
        for r in work(migrated, "dropped")
        if r["entity"] == "doi_mapping"
    }
    assert dropped == {
        3: "held_by_conflict",
        4: "held_by_conflict",
        5: "held_by_conflict",
        6: "shadowed",
    }
    found = {(c["kind"], c["ref"]) for c in work(migrated, "conflict")}
    assert ("doi_mapping_cycle", "10.5281/zenodo.3001") in found
    assert ("doi_mapping_dangling", "10.5281/zenodo.997") in found
    urls = [
        (u["kind"], u["path"], u["target"], u["status"], u["ref"])
        for u in work(migrated, "legacy_url", "id")
    ]
    assert urls == [
        (
            "doi",
            "/doi/10.5281/zenodo.999/",
            "/doi/10.5281/zenodo.1001/",
            308,
            "doi_mapping:1",
        ),
        (
            "doi",
            "/doi/10.5281/zenodo.998/",
            "/doi/10.5281/zenodo.1001/",
            308,
            "doi_mapping:2",
        ),
        (
            "hubfile_name",
            "/hubfiles/raw/14/dup.uvl",
            "/hubfiles/raw/14/dup~14.uvl",
            308,
            "hubfiles:14",
        ),
    ]


def test_e6_holds_the_notices_of_the_move_until_rb2_ends(migrated):
    notices = work(migrated, "held_notice", "id")
    assert [(n["kind"], n["ref"], n["recipient"]) for n in notices] == [
        ("transfer_cancelled", "dataset_transfer_request:1", "alice@uvlhub.test"),
        ("transfer_cancelled", "dataset_transfer_request:1", "bob@uvlhub.test"),
        ("api_keys_carried_over", "user:1", "alice@uvlhub.test"),
        ("api_keys_carried_over", "user:2", "bob@uvlhub.test"),
        ("api_keys_carried_over", "user:3", "jose@uvlhub.test"),
        ("api_keys_carried_over", "user:4", "mar@uvlhub.test"),
    ]
    assert {n["hold_until"] for n in notices} == {"end of RB-2"}
    offer = notices[0]
    assert (
        offer["subject"]
        == "Your offer to transfer “Dataset 1” (10.5281/zenodo.1001) was cancelled"
    )
    assert "uvlhub.io moved to uvlhub 3.0 on 2026-11-20" in offer["body_text"]
    assert "uvlhub.io pasó a uvlhub 3.0 el 2026-11-20" in offer["body_text"]
    bob = notices[3]["body_text"]
    assert "revoked, as it allowed nothing (it had no scopes)." in bob
    assert "revoked, as it was never used." in bob
    alice = notices[2]["body_text"]
    assert "works until 2027-11-20." in alice and "works until 2027-02-18." in alice
    # No link that carries a token: mail would send it once and keep it cut.
    assert not any("://" in n["body_text"] for n in notices)


# ── Rules ────────────────────────────────────────────────────────────────


def _mapping(i, old, new):
    return {"id": i, "dataset_doi_old": old, "dataset_doi_new": new}


def test_a_chain_of_mappings_ends_where_a_dataset_is_and_a_cycle_nowhere():
    mappings = [
        _mapping(1, "a", "b"),
        _mapping(2, "b", "c"),
        _mapping(3, "x", "y"),
        _mapping(4, "y", "x"),
        _mapping(5, "z", "x"),
        _mapping(6, "q", "nowhere"),
        _mapping(7, "a", "c"),
        _mapping(8, None, "c"),
    ]
    loads, shadowed, cycles, dangling = follow_mappings(mappings, {"c"})
    assert [(r["id"], r["dataset_doi_new"]) for r in loads] == [(1, "c"), (2, "c")]
    assert [(r["id"], by) for r, by in shadowed] == [(7, 1), (8, None)]
    assert [[r["id"] for r in cycle] for cycle in cycles] == [[3, 4]]
    # z runs into the cycle; q ends at a DOI no dataset has.
    assert sorted(r["id"] for r in dangling) == [5, 6]


@pytest.mark.parametrize(
    "name, expected",
    [
        ("dup.uvl", "dup~14.uvl"),
        ("model.tar.gz", "model.tar~14.gz"),
        ("README", "README~14"),
        (".uvl", ".uvl~14"),
        ("m" * 118 + ".uvl", "m" * 113 + "~14.uvl"),
    ],
)
def test_dm10_puts_the_id_before_the_extension_within_the_column(name, expected):
    renamed = rules.suffixed_name(name, 14, 120)
    assert renamed == expected and len(renamed) <= 120


def _snapshot(record):
    text = json.dumps(record)
    return {"record": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}


def test_a_tombstone_is_dated_by_its_record_only_when_it_validates():
    record = dict(synthetic.ORPHAN_RECORD)
    doi = synthetic.ORPHAN_DOI
    assert rules.zenodo_dates(_snapshot(record), doi) == (
        datetime(2025, 3, 1, 10, 0),
        datetime(2025, 3, 2),
    )
    assert rules.zenodo_dates(_snapshot(record), doi.upper() + " ") is not None
    assert rules.zenodo_dates(None, doi) is None
    assert rules.zenodo_dates(_snapshot(record), "10.5281/zenodo.1") is None
    tampered = dict(_snapshot(record), sha256="0" * 64)
    assert rules.zenodo_dates(tampered, doi) is None
    undated = {"doi": doi, "metadata": {}}
    assert rules.zenodo_dates(_snapshot(undated), doi) is None
    only_day = {"doi": doi, "metadata": {"publication_date": "2024-05-06"}}
    assert rules.zenodo_dates(_snapshot(only_day), doi) == (
        datetime(2024, 5, 6),
        datetime(2024, 5, 6),
    )
