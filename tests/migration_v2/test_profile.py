"""E2: the source against the clean v2.12 (P-00), the probes and the rule of
each, and the decisions held to the rows they were taken on.

The rehearsal (migrated) reads a source made from the very schema E2
compares it with, so it finds no drift; the tests that drift it, or decide,
run on schemas of their own (isolated). A run that went through stands for
a 3.0 that may have opened, so the runs after it are forced, with a B2.
"""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
import sqlalchemy as sa

from uvlhub_splent.migration_v2.db import make_engine
from uvlhub_splent.migration_v2.ledger import fingerprint
from uvlhub_splent.migration_v2.params import Refused
from uvlhub_splent.migration_v2.pipeline import run
from uvlhub_splent.migration_v2.profile import (
    PROBES,
    build_reference,
    read_sources,
    schema_drift,
)


def rows(engine, sql, **params):
    with engine.connect() as connection:
        return [
            dict(row) for row in connection.execute(sa.text(sql), params).mappings()
        ]


def execute(engine, *statements):
    with engine.connect() as connection:
        for statement in statements:
            connection.execute(sa.text(statement))
        connection.commit()


@pytest.fixture
def again(tmp_path):
    """The params of a run after one that went through: forced, with a B2
    taken just now."""

    def make(params, **overrides):
        b2 = tmp_path / "b2.sql"
        b2.write_text("-- B2, taken just now\n")
        return replace(params, force=True, b2=b2, **overrides)

    return make


def decide(engine, params, kind, resolution="accept"):
    """Decide the conflicts of ``kind`` as the docs say: their kind, ref,
    rows and fingerprint copied from uvlhub_migration.conflict."""
    execute(
        engine,
        f"INSERT INTO `{params.inputs_schema}`.decision "
        "(kind, ref, source_rows, fingerprint, resolution, note, author, decided_at) "
        "SELECT kind, ref, source_rows, fingerprint, "
        f"'{resolution}', 'seen', 'tests/migration_v2', UTC_TIMESTAMP() "
        f"FROM `{params.work_schema}`.conflict WHERE kind = '{kind}'",
    )


# ── The rehearsal ────────────────────────────────────────────────────────


def test_every_probe_has_a_rule_but_the_ones_that_must_find_nothing():
    assert {p.name for p in PROBES if p.rule is None} == {"P-17b", "P-27b"}
    assert len({p.name for p in PROBES}) == len(PROBES)


def test_the_rehearsal_profiles_the_source(migrated):
    profile = migrated.report["profile"]
    assert migrated.report["facts"]["schema_drift"] == 0
    expected = {
        "P-01": 3,  # metadata 290 and 292, with a DOI, and 291
        "P-02": 3,  # author 6, of no metadata, 7 of 290 and 9 of 292
        "P-03": 1,  # 10.5281/zenodo.1011
        "P-04b": 1,  # dataset 1, origin of 2 and 14
        "P-07": 1,  # dataset 13's dup.uvl
        "P-12b": 1,  # alice on her own dataset 1
        "P-17b": 0,
        "P-21": 1,  # 16 and 17
        "P-25": 2,  # the seed's two accounts
        "P-25b": 3,  # the sandbox's, the seed's and dataset 10's
        "P-25c": 2,  # checksum12 and deadbeef
        "P-26": 5,  # josé, már, not a link, and two for no account
        "P-27b": 0,
        "P-28": 2,  # the trigger and the view
    }
    assert {name: profile[name] for name in expected} == expected
    kept = {
        row["name"]: row
        for row in rows(
            migrated.engine,
            f"SELECT * FROM `{migrated.params.work_schema}`.profile",
        )
    }
    assert set(kept) == {probe.name for probe in PROBES}
    assert json.loads(kept["P-03"]["detail"]) == [
        {"dataset_doi": "10.5281/zenodo.1011", "n": 2}
    ]


def test_a_conflict_names_the_rows_its_fingerprint_is_of(migrated):
    """What a decision copies is enough to read the rows again (E2)."""
    conflict = rows(
        migrated.engine,
        f"SELECT * FROM `{migrated.params.work_schema}`.conflict "
        "WHERE kind = 'doi_not_zenodo'",
    )
    refs = json.loads(conflict[0]["source_rows"])
    assert refs == ["ds_meta_data:208"]
    engine = make_engine(
        migrated.params.server.host,
        3306,
        migrated.params.server.user,
        migrated.params.server.password,
    )
    with engine.connect() as connection:
        sources = read_sources(connection, migrated.params.source_schema, refs)
    engine.dispose()
    assert sources["ds_meta_data"][0]["dataset_doi"] == "10.5072/zenodo.55"
    assert fingerprint(sources) == conflict[0]["fingerprint"]


# ── P-00 ─────────────────────────────────────────────────────────────────


def test_p00_names_every_difference_with_the_clean_v2_12(isolated, root_engine):
    params = isolated("p00")
    engine = make_engine(
        params.server.host, 3306, params.server.user, params.server.password
    )
    for schema in (params.reference_schema, params.source_schema):
        with engine.connect() as connection:
            build_reference(connection, schema)
    src = f"`{params.source_schema}`"
    execute(
        root_engine,
        f"ALTER TABLE {src}.author ADD COLUMN fm_meta_data_id INT NULL",
        f"ALTER TABLE {src}.`user` MODIFY email VARCHAR(256) COLLATE utf8mb4_bin NULL",
        f"ALTER TABLE {src}.api_keys DROP INDEX `key`",
        f"CREATE TABLE {src}.fm_meta_data (id INT PRIMARY KEY)",
    )
    with engine.connect() as connection:
        drifts = schema_drift(connection, params.source_schema, params.reference_schema)
    engine.dispose()
    assert [(d.ref, d.detail) for d in drifts] == [
        ("fm_meta_data", "a table the clean v2.12 does not have"),
        ("author.fm_meta_data_id", "a column the clean v2.12 does not have"),
        (
            "user.email",
            "coll 'utf8mb4_bin' where the clean v2.12 has 'utf8mb4_uca1400_ai_ci'",
        ),
        (
            "api_keys index (key)",
            "an index of the clean v2.12 the source does not have",
        ),
    ]


# ── Decisions ────────────────────────────────────────────────────────────


def test_e2_stops_at_a_drift_until_a_decision_accepts_it(
    isolated, synthetic_dump, seedless, root_engine, again
):
    params = isolated("drift", dump=synthetic_dump, stages=("E0", "E1"))
    run(params)
    execute(
        root_engine,
        f"ALTER TABLE `{params.source_schema}`.author "
        "ADD COLUMN fm_meta_data_id INT NULL",
    )
    profiling = again(params, stages=("E0", "E2"))
    with pytest.raises(Refused) as refusal:
        run(profiling)
    assert refusal.value.stage == "E2"
    assert "1 open conflict(s) of kind schema_drift" in refusal.value.reasons

    decide(root_engine, params, "schema_drift")
    report = run(again(params, stages=("E0", "E2")))
    assert report["decided"] == {"schema_drift": 1}
    assert report["decisions"]["unused"] == []

    # The drift gone, the decision accepts what is not there any more.
    execute(
        root_engine,
        f"ALTER TABLE `{params.source_schema}`.author DROP COLUMN fm_meta_data_id",
    )
    with pytest.raises(Refused) as refusal:
        run(again(params, stages=("E0", "E2")))
    assert refusal.value.reasons == [
        "decision 1 (schema_drift author.fm_meta_data_id): P-00 finds that drift no more"
    ]


def test_a_decision_closes_its_conflict_while_its_rows_stay_the_same(
    isolated, synthetic_dump, seedless, root_engine, again
):
    params = isolated(
        "decide",
        dump=synthetic_dump,
        stages=("E0", "E1", "E2", "E3", "E4", "E5"),
        allow_open_conflicts=True,
    )
    first = run(params)
    assert first["conflicts"]["doi_not_zenodo"] == 1
    decide(root_engine, params, "doi_not_zenodo")

    report = run(again(params))
    assert "doi_not_zenodo" not in report["conflicts"]
    assert report["decided"] == {"doi_not_zenodo": 1}
    closed = rows(
        root_engine,
        f"SELECT status, decision_id FROM `{params.work_schema}`.conflict "
        "WHERE kind = 'doi_not_zenodo'",
    )
    assert closed == [{"status": "decided", "decision_id": 1}]

    # A resolution the migrator does not know stops E2.
    decide(root_engine, params, "doi_repeated", resolution="merge")
    with pytest.raises(Refused) as refusal:
        run(again(params))
    assert refusal.value.reasons == [
        "decision 2 (doi_repeated 10.5281/zenodo.1011): resolution 'merge' is none of accept"
    ]
    execute(root_engine, f"DELETE FROM `{params.inputs_schema}`.decision WHERE id = 2")

    # The rows it was taken on change: E2 stops, rehearsal or not.
    execute(
        root_engine,
        f"UPDATE `{params.source_schema}`.ds_meta_data SET title = 'Edited' WHERE id = 208",
    )
    with pytest.raises(Refused) as refusal:
        run(again(params, stages=("E0", "E2")))
    assert refusal.value.stage == "E2"
    assert refusal.value.reasons == [
        "decision 1 (doi_not_zenodo 10.5072/zenodo.55): the rows it was taken on "
        "(ds_meta_data:208) changed, or are not there any more"
    ]


def test_e2_stops_at_what_no_rule_handles(
    isolated, synthetic_dump, seedless, root_engine, again
):
    """P-27b: production lets a NULL in where the chain does not, and the
    contract has no on_null for it: zero unknowns, rehearsal or not."""
    params = isolated("unruled", dump=synthetic_dump, stages=("E0", "E1"))
    run(params)
    src = f"`{params.source_schema}`"
    execute(
        root_engine,
        f"ALTER TABLE {src}.user_profile MODIFY name VARCHAR(100) NULL",
        f"UPDATE {src}.user_profile SET name = NULL WHERE id = 101",
    )
    with pytest.raises(Refused) as refusal:
        run(again(params, stages=("E0", "E2"), allow_open_conflicts=True))
    assert refusal.value.stage == "E2"
    assert len(refusal.value.reasons) == 1
    assert refusal.value.reasons[0].startswith(
        "P-27b NULLs the target refuses, without a rule: 1 found"
    )
