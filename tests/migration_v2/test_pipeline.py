"""The rehearsal of the whole pipeline on the dirty v2.12 (R0): what each
stage did, read back from uvlhub3, the work schema and the store.

synthetic.py says who is who. The run goes on past open conflicts, as a
rehearsal does; test_strict_* show the cutover stopping at them.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import timedelta

import pytest
import sqlalchemy as sa

from uvlhub_splent.migration_v2 import contract as contract_module
from uvlhub_splent.migration_v2 import rules
from uvlhub_splent.migration_v2.verify import empty_tables, foreign_key_orphans
from uvlhub_splent.migration_v2.params import Refused
from uvlhub_splent.migration_v2.pipeline import run

from . import synthetic

T0 = synthetic.T0


def rows(migrated, sql, **params):
    with migrated.engine.connect() as connection:
        return [
            dict(row) for row in connection.execute(sa.text(sql), params).mappings()
        ]


def target(migrated, table, order="id", where="1"):
    return rows(
        migrated,
        f"SELECT * FROM `{migrated.params.target_schema}`.`{table}` WHERE {where} ORDER BY {order}",
    )


def work(migrated, table, where="1"):
    return rows(
        migrated,
        f"SELECT * FROM `{migrated.params.work_schema}`.`{table}` WHERE {where}",
    )


def by_id(items, key="id"):
    return {item[key]: item for item in items}


def dropped(migrated, entity):
    return {
        r["ref_id"]: r["reason"]
        for r in work(migrated, "dropped", f"entity = '{entity}'")
    }


def conflicts(migrated):
    return {(c["kind"], c["ref"]) for c in work(migrated, "conflict")}


# ── The run ──────────────────────────────────────────────────────────────


def test_the_rehearsal_runs_every_stage_this_pass_has(migrated):
    report = migrated.report
    assert report["stages_run"] == ["E0", "E1", "E3", "E4", "E5", "E7", "E8", "E10"]
    assert set(report["stages_not_yet"]) == {"E2", "E6", "E9"}
    assert report["stopped"] is None
    assert report["e5_first_pass"]["first_pass"] is True
    assert report["ready_for_cutover"] is False


def test_no_orm_listener_fires_during_the_load(migrated):
    """§3.4: the migrator writes with Core on its own connections, so not one
    session or mapper event of a feature fires (DSMetrics' after_insert,
    hubfile's Session.after_commit). E3 and E8 run the features' commands in
    processes of their own, where their listeners are theirs."""
    assert migrated.fired == []


def test_the_report_is_written_and_signed(migrated):
    written = json.loads(migrated.params.report.read_text())
    assert written["signature"]["operator"] == "tests/migration_v2"
    assert written["signature"]["sha256"] == migrated.report["signature"]["sha256"]
    run_row = work(migrated, "run")[0]
    assert run_row["status"] == "completed" and run_row["completed_at"] is not None
    assert (
        run_row["dump_sha256"]
        == hashlib.sha256(migrated.params.dump.read_bytes()).hexdigest()
    )


# ── E1 ───────────────────────────────────────────────────────────────────


def test_e1_restores_the_dump_and_drops_what_should_not_be_there(migrated):
    facts = migrated.report["facts"]
    assert facts["source_head"] == "e5f6a7b8c9d0"
    assert sorted(facts["p28_objects"]) == ["trigger planted", "view planted_view"]
    left = rows(
        migrated,
        "SELECT trigger_name FROM information_schema.triggers WHERE trigger_schema = :s "
        "UNION ALL SELECT table_name FROM information_schema.views WHERE table_schema = :s",
        s=migrated.params.source_schema,
    )
    assert left == []
    assert facts["source_counters"]["user"] == synthetic.COUNTERS["user"]
    assert (
        len(rows(migrated, f"SELECT id FROM `{migrated.params.source_schema}`.`user`"))
        == 15
    )


def test_e1_refuses_a_dump_at_another_head(isolated, synthetic_dump, seedless):
    params = isolated(
        "head", dump=synthetic_dump, expected_head="f7a8b9c0d1e2", stages=("E0", "E1")
    )
    with pytest.raises(Refused) as refusal:
        run(params)
    assert refusal.value.stage == "E1"
    assert refusal.value.reasons == [
        "the dump is at e5f6a7b8c9d0, MIGRATION_EXPECTED_HEAD is f7a8b9c0d1e2 (P-19)"
    ]


# ── E4: identity ─────────────────────────────────────────────────────────


def test_e4_loads_the_accounts_but_the_seed_and_the_clashes(migrated):
    users = by_id(target(migrated, "user"))
    assert sorted(users) == [1, 2, 3, 4, 7, 8, 9, 12, 13, 14, 15]
    assert dropped(migrated, "user") == {
        5: "seed",
        6: "seed",
        10: "held_by_conflict",
        11: "held_by_conflict",
    }
    assert ("email_clash_collation", "10,11") in conflicts(migrated)
    source = by_id(synthetic.users())
    for user in users.values():
        assert user["account_origin"] == "legacy_v2"
        assert user["session_version"] == 2
        assert user["email_canonical"] == (
            user["email"].lower() if user["email"] else None
        )
        assert user["created_at"] == source[user["id"]]["created_at"]
    assert users[1]["role"] == "admin"
    assert {u["role"] for i, u in users.items() if i != 1} == {"user"}
    assert users[7]["disabled_at"] == T0
    assert users[8]["email"] is None


def test_e4_confirms_an_address_only_with_a_positive_proof(migrated):
    users = by_id(target(migrated, "user"))
    proved = {
        i: (u["email_verified_via"], u["email_verified_at"])
        for i, u in users.items()
        if u["email_verified_at"]
    }
    assert proved == {
        1: ("legacy_reset", T0 - timedelta(days=200)),
        2: ("legacy_github", synthetic.external_identities()[1]["created_at"]),
        4: ("legacy_reset", T0 - timedelta(days=50)),
    }


def test_e4_a_probable_takeover_loads_unconfirmed_and_must_reset(migrated):
    jose = by_id(target(migrated, "user"))[3]
    assert jose["email_verified_at"] is None
    assert jose["password"] == rules.UNUSABLE_PASSWORD
    assert jose["has_usable_password"] == 0
    candidates = {c["user_id"]: c for c in work(migrated, "takeover_candidate")}
    assert (
        candidates[3]["kind"] == "probable"
        and candidates[3]["typed"] == "josé@uvlhub.test"
    )
    assert (
        candidates[4]["kind"] == "attempt"
        and candidates[4]["typed"] == "már@uvlhub.test"
    )


def test_e4_an_account_opened_by_a_provider_has_no_usable_password(migrated):
    users = by_id(target(migrated, "user"))
    usable = {i for i, u in users.items() if u["has_usable_password"]}
    assert usable == {1, 4, 7, 9, 12, 13, 14, 15}


def test_e4_profiles_are_stripped_and_follow_their_account(migrated):
    profiles = by_id(target(migrated, "user_profile"))
    assert (
        profiles[101]["name"] == "Alice"
        and profiles[101]["affiliation"] == "Universidad de Sevilla"
    )
    assert dropped(migrated, "user_profile") == {
        105: "seed",
        106: "seed",
        110: "held_by_conflict",
        111: "held_by_conflict",
    }


def test_e4_folds_orcid_and_github_into_external_identity(migrated):
    identities = by_id(target(migrated, "external_identity"))
    # alice's: the earlier date of the two, and the iD as its username.
    assert identities[1]["created_at"] == synthetic.orcids()[0]["registration_date"]
    assert identities[1]["provider_username"] == synthetic.ALICE_ORCID
    # bob's: the GitHub address is his own, so it is kept as the proof.
    assert identities[2]["provider_email_verified"] == "bob@uvlhub.test"
    # Folded in with new ids, above the source's counter.
    new = {
        i: (r["user_id"], r["provider"], r["provider_id"])
        for i, r in identities.items()
        if i >= 50
    }
    assert new == {50: (3, "orcid", synthetic.JOSE_ORCID), 51: (14, "github", "2001")}
    assert identities[51]["provider_username"] == "erin-gh"
    assert dropped(migrated, "external_identity") == {
        5: "held_by_conflict",
        6: "held_by_conflict",
        7: "held_by_conflict",
    }
    assert dropped(migrated, "orcid") == {
        2: "held_by_conflict",
        3: "held_by_conflict",
        4: "orphan",
        5: "held_by_conflict",
    }
    found = conflicts(migrated)
    assert {
        ("identity_second_identity", "2"),
        ("identity_other_account", "3"),
        ("identity_invalid_id", "5"),
        ("identity_second_link", "13:github"),
    } <= found
    pairs = rows(
        migrated,
        f"SELECT user_id, provider, COUNT(*) n FROM `{migrated.params.target_schema}`.external_identity "
        "GROUP BY user_id, provider HAVING n > 1",
    )
    assert pairs == []


def test_e4_converts_the_keys_as_d12_says(migrated):
    tokens = by_id(target(migrated, "api_token"))
    keys = by_id(synthetic.api_keys())
    assert sorted(tokens) == [1, 2, 3, 4, 5, 6, 7, 9]
    assert dropped(migrated, "api_keys") == {8: "seed"}
    for token_id, token in tokens.items():
        key = keys[token_id]["key"]
        assert token["token_hash"] == hashlib.sha256(key.encode()).hexdigest()
        assert token["prefix"] == key[:15]
    revoked = {i: t["revoked_reason"] for i, t in tokens.items() if t["revoked_at"]}
    assert revoked == {
        3: "import_no_scopes",
        4: "import_never_used",
        6: "import_unused",
    }
    assert tokens[1]["expires_at"] == T0 + timedelta(days=365)
    assert tokens[2]["expires_at"] == T0 + timedelta(days=90)
    assert (
        tokens[7]["created_at"] == keys[7]["last_used_at"]
        and tokens[7]["name"] == "uvlhub 2 key"
    )
    assert tokens[1]["name"] == f"uvlhub 2 key ({keys[1]['created_at']:%Y-%m-%d})"
    assert tokens[9]["scopes"] == "read_dataset"


# ── E5: content (first pass) ─────────────────────────────────────────────


def test_e5_loads_the_datasets_with_the_state_their_metadata_implies(migrated):
    datasets = by_id(target(migrated, "datasets"))
    assert sorted(datasets) == [1, 2, 3, 4, 5, 7, 8, 9, 10, 13, 14]
    assert dropped(migrated, "datasets") == {
        6: "ghost_draft",
        11: "held_by_conflict",
        12: "seed",
    }
    state = {i: (d["status"], d["visibility"]) for i, d in datasets.items()}
    assert state[1] == ("published", "public")
    assert state[3] == ("sync_pending", "public")
    assert state[4] == ("failed", "public")
    assert state[5] == ("draft", "public")
    assert state[7] == ("published", "anonymous")
    assert state[9] == ("published", "public")
    assert (
        datasets[1]["published_at"] == datasets[1]["created_at"]
        and datasets[5]["published_at"] is None
    )
    assert datasets[4]["publisher_record_id"] == "1007"
    assert datasets[2]["dataset_origin_id"] == 1 and datasets[2]["dataset_version"] == 2
    assert {
        i: d["feature_model_count"] for i, d in datasets.items() if i in (1, 5, 13)
    } == {1: 2, 5: 2, 13: 3}


def test_e5_keeps_an_anonymous_datasets_authors_apart(migrated):
    meta = by_id(target(migrated, "ds_meta_data"))[207]
    assert json.loads(meta["private_authors"]) == [
        {
            "name": "Carol Danvers",
            "affiliation": "Kree",
            "orcid": synthetic.CAROL_ORCID,
        },
        {"name": "Hidden Two", "affiliation": None, "orcid": None},
    ]
    authors = by_id(target(migrated, "author"))
    assert sorted(authors) == [1, 2, 3]
    assert authors[1]["orcid"] == synthetic.ALICE_ORCID and authors[2]["orcid"] is None
    assert dropped(migrated, "author") == {6: "orphan", 7: "tombstone", 8: "seed"}
    mapped = work(migrated, "id_map", "entity = 'author'")
    assert {m["source_id"] for m in mapped} == {4, 5}


def test_e5_orphan_metadata_becomes_a_tombstone_or_goes(migrated):
    assert [(t["doi"], t["ds_meta_data_id"]) for t in work(migrated, "tombstone")] == [
        (synthetic.ORPHAN_DOI, 290)
    ]
    reasons = dropped(migrated, "ds_meta_data")
    assert (
        reasons[290] == "tombstone"
        and reasons[291] == "orphan"
        and reasons[212] == "seed"
    )
    publisher = by_id(target(migrated, "ds_meta_data"))[204]["api_publisher_user_id"]
    assert publisher is None


def test_e5_leaves_the_content_faults_open_as_conflicts(migrated):
    found = conflicts(migrated)
    assert ("doi_not_zenodo", "10.5072/zenodo.55") in found
    assert ("doi_repeated", "10.5281/zenodo.1011") in found
    assert ("lineage_branch", "1") in found
    assert ("duplicate_path", "13:/dup.uvl") in found
    assert ("checksum_unknown", "15") in found


def test_e5_files_and_feature_models(migrated):
    files = by_id(target(migrated, "hubfiles"))
    assert dropped(migrated, "hubfiles") == {11: "held_by_conflict", 12: "seed"}
    assert files[3]["checksum_algo"] == "md5" and files[1]["checksum_algo"] == "sha256"
    assert files[15]["checksum_algo"] is None
    assert {f["artifact_type"] for f in files.values()} == {"uvl"}
    models = by_id(target(migrated, "feature_model"))
    assert models[66]["dataset_id"] == 5  # its file's dataset (C-07)
    metrics = target(migrated, "hubfile_metrics", order="hubfile_id")
    assert [(m["hubfile_id"], m["features"]) for m in metrics] == [(1, 2)]
    assert target(migrated, "hubfile_factlabel", order="hubfile_id") == []


def test_e5_moves_votes_to_the_root_and_drops_self_votes(migrated):
    ratings = by_id(target(migrated, "dataset_rating"))
    assert {i: (r["user_id"], r["dataset_id"]) for i, r in ratings.items()} == {
        2: (2, 1),
        4: (12, 1),
        5: (3, 7),
    }
    assert dropped(migrated, "dataset_rating") == {
        1: "duplicate_on_root",
        3: "self_vote",
        6: "seed",
    }


def test_e5_cancels_the_pending_offers(migrated):
    offers = by_id(target(migrated, "dataset_transfer_request"))
    assert offers[1]["status"] == "CANCELLED" and offers[1]["resolved_at"] == T0
    assert offers[2]["status"] == "DECLINED"
    assert dropped(migrated, "dataset_transfer_request") == {3: "seed"}


# ── E7 ───────────────────────────────────────────────────────────────────


def test_e7_gives_every_table_its_counter_with_the_margin(migrated):
    counters = dict(
        (r["table_name"], r["auto_increment"])
        for r in rows(
            migrated,
            "SELECT table_name, auto_increment FROM information_schema.tables WHERE table_schema = :s",
            s=migrated.params.target_schema,
        )
    )
    for table, given in migrated.report["facts"]["counters_given"].items():
        assert given == 10000 and counters[table] >= given


def test_e7_checks_pass_but_the_ones_this_pass_cannot_meet(migrated):
    checks = {c["name"]: c for c in migrated.report["checks"]}
    failing = {name for name, c in checks.items() if not c["ok"]}
    # V-08: dataset 3 is published and its file is in mismatch (recovery
    # from Zenodo is not in this pass); V-09: the branch of dataset 1 waits
    # for the repair by concept DOI.
    assert failing == {"V-08", "V-09"}
    assert not checks["V-09"]["blocking"]
    for name in (
        "V-01",
        "V-02",
        "V-03",
        "V-04",
        "V-05",
        "V-06",
        "V-07",
        "V-10",
        "V-11",
        "V-15",
        "empty-tables",
    ):
        assert checks[name]["ok"], name


# ── E8: files ────────────────────────────────────────────────────────────


def test_e8_links_every_file_to_its_key_and_says_what_it_found(migrated):
    store = migrated.params.store_root
    files = by_id(target(migrated, "hubfiles"))
    status = {i: f["storage_status"] for i, f in files.items()}
    assert (
        status[4] == "mismatch"
        and status[6] == "missing"
        and status[15] == "unverified"
    )
    assert {s for i, s in status.items() if i not in (4, 6, 15)} == {"ok"}
    for hubfile_id, row in files.items():
        if row["storage_status"] != "ok":
            continue
        path = store / row["storage_key"]
        assert row["storage_key"] == f"datasets/{row['dataset_id']}/src/{hubfile_id}"
        assert path.stat().st_nlink >= 2  # a hard link to the mirror, not a copy
        assert row["content_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert not (store / "user_1").exists()


def test_e8_writes_the_manifest_with_what_no_row_names(migrated):
    manifest = work(migrated, "file_manifest")
    loose = {m["path"]: m["status"] for m in manifest if m["hubfile_id"] is None}
    assert loose == {
        "temp/1/half.uvl": "temp",
        "user_1/dataset_1/glencoe/model one.json": "derived",
        "user_1/dataset_99/uvl/lost.uvl": "orphan",
        "user_11/dataset_11/uvl/held.uvl": "orphan",
        "user_5/dataset_12/uvl/file1.uvl": "orphan",
    }
    rows_ = {m["hubfile_id"]: m for m in manifest if m["hubfile_id"]}
    assert rows_[2]["path"] == "user_1/dataset_1/uvl/sub dir/a#b/b#2.uvl"
    assert rows_[6]["status"] == "missing"
    assert ("file_mismatch", "4") in conflicts(migrated)


# ── The cutover's run, and a second one ──────────────────────────────────


def test_e3_refuses_a_schema_that_is_not_the_contracts(
    isolated, synthetic_dump, seedless
):
    """V-12 and V-14 on a real uvlhub3: a contract that expects another head
    and another collation than the pinned features give stops E3."""
    contract = contract_module.load()
    user = contract.tables["user"]
    email = replace(user.columns["email"], collation="utf8mb4_bin")
    tables = dict(
        contract.tables, user=replace(user, columns=dict(user.columns, email=email))
    )
    features = dict(
        contract.features,
        splent_feature_rating={
            **contract.features["splent_feature_rating"],
            "head": "rating0002",
        },
    )
    drifted = replace(contract, tables=tables, features=features)
    params = isolated("drift", dump=synthetic_dump, stages=("E0", "E1", "E3"))
    with pytest.raises(Refused) as refusal:
        run(params, drifted)
    assert refusal.value.stage == "E3"
    assert refusal.value.reasons == [
        "V-12 splent_feature_rating at 3e72750db961, the contract expects rating0002",
        "V-14 user.email: utf8mb4_unicode_ci, the contract says utf8mb4_bin",
        "user.email: collation utf8mb4_unicode_ci, the contract says utf8mb4_bin",
    ]


def test_e7_finds_what_the_load_let_in_with_the_checks_off(migrated):
    """V-04 and the empty tables, on rows written the way a batch is, with
    the foreign keys off, and taken back."""
    schema = migrated.params.target_schema
    with migrated.engine.connect() as connection:
        connection.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0")
        connection.execute(
            sa.text(
                f"INSERT INTO `{schema}`.user_profile (id, user_id, name, surname) "
                "VALUES (9999, 9999, 'No', 'Account')"
            )
        )
        connection.execute(
            sa.text(
                f"INSERT INTO `{schema}`.auth_token (user_id, purpose, token_hash, created_at, expires_at) "
                "VALUES (1, 'reset', 'x', '2026-01-01', '2026-01-02')"
            )
        )
        orphans = foreign_key_orphans(connection, schema)
        filled = empty_tables(connection, schema, contract_module.load())
        connection.rollback()
        connection.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1")
    assert orphans == {"user_profile.user_id -> user": 1}
    assert filled == {"auth_token": 1}


def test_e8_refuses_without_the_mirror(isolated, synthetic_dump, seedless, tmp_path):
    params = isolated(
        "nomirror",
        dump=synthetic_dump,
        store_root=tmp_path,
        allow_open_conflicts=True,
        stages=("E0", "E1", "E3", "E4", "E5", "E8"),
    )
    with pytest.raises(Refused) as refusal:
        run(params)
    assert refusal.value.stage == "E8"
    assert refusal.value.reasons == [
        f"no mirror of v2.12's uploads/ at {tmp_path / '.legacy_mirror'}"
    ]


def test_the_listener_spy_hears_the_orm():
    """The control of test_no_orm_listener_fires_during_the_load: the same
    spy, around an ORM write, hears it."""
    from sqlalchemy.orm import DeclarativeBase, Session

    from .conftest import ListenerSpy

    class Base(DeclarativeBase):
        pass

    class Thing(Base):
        __tablename__ = "thing"
        id = sa.Column(sa.Integer, primary_key=True)

    engine = sa.create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with ListenerSpy() as spy, Session(engine) as session:
        session.add(Thing(id=1))
        session.commit()
    assert {
        "Session.before_flush",
        "Session.after_commit",
        "Mapper.before_insert",
    } <= set(spy.fired)


def test_strict_the_cutover_stops_at_an_open_conflict(
    isolated, synthetic_dump, seedless
):
    params = isolated(
        "strict", dump=synthetic_dump, stages=("E0", "E1", "E3", "E4", "E5")
    )
    with pytest.raises(Refused) as refusal:
        run(params)
    assert refusal.value.stage == "E4"
    assert "1 open conflict(s) of kind email_clash_collation" in refusal.value.reasons
    assert refusal.value.report["stopped"]["stage"] == "E4"


def _digest(migrated, contract_tables):
    digests = {}
    with migrated.engine.connect() as connection:
        for table in contract_tables:
            data = connection.execute(
                sa.text(
                    f"SELECT * FROM `{migrated.params.target_schema}`.`{table}` ORDER BY 1"
                )
            ).all()
            digests[table] = hashlib.sha256(repr(data).encode()).hexdigest()
    return digests


def test_a_second_run_is_refused_then_forced_and_gives_the_same_database(
    migrated, tmp_path
):
    """Principles 2 and 3, and E0: the run that completed stands for a 3.0
    that may have opened, so a second one needs --force and a fresh B2; then
    it starts over and writes the very same rows."""
    tables = [t.name for t in contract_module.load().by_role(contract_module.LOAD)]
    before = _digest(migrated, tables)
    with pytest.raises(Refused) as refusal:
        run(migrated.params)
    assert refusal.value.stage == "E0"
    assert any("migration.completed" in reason for reason in refusal.value.reasons)

    b2 = tmp_path / "b2.sql"
    b2.write_text("-- B2, taken just now\n")
    run(replace(migrated.params, force=True, b2=b2))
    assert _digest(migrated, tables) == before
