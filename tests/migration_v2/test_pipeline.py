"""The rehearsal of the whole pipeline on the dirty v2.12 (R0): what each
stage did, read back from uvlhub3, the work schema and the store.

synthetic.py says who is who. The run goes on past open conflicts, as a
rehearsal does; test_strict_* show the cutover stopping at them.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timedelta

import pytest
import sqlalchemy as sa

from uvlhub_splent.migration_v2 import contract as contract_module
from uvlhub_splent.migration_v2.verify import empty_tables, foreign_key_orphans
from uvlhub_splent.migration_v2.derived import REWRITTEN
from uvlhub_splent.migration_v2.params import Refused
from uvlhub_splent.migration_v2.pipeline import run
from uvlhub_splent.migration_v2.schema import child_env

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


def test_the_rehearsal_runs_every_stage(migrated):
    report = migrated.report
    assert report["stages_run"] == [
        "E0",
        "E1",
        "E2",
        "E3",
        "E4",
        "E5",
        "E6",
        "E7",
        "E8",
        "E9",
        "E10",
    ]
    assert report["stages_not_yet"] == {}
    assert report["stopped"] is None
    # E5 is its final pass; the rehearsal leaves conflicts open, and DM-1
    # is not checked (test_e7_checks_pass_and_what_keeps_the_cutover_off).
    assert report["e5_first_pass"] == {"first_pass": False, "deferred": []}
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
    assert len(
        rows(migrated, f"SELECT id FROM `{migrated.params.source_schema}`.`user`")
    ) == len(synthetic.users())


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


def test_e1_reads_b0_and_e5_quarantines_the_originals_the_hotfix_rewrote(
    isolated, hotfix_dumps, root_engine, seedless
):
    """C-29: on a source at the hotfix's head the descriptions are what its
    revision left, and B0 has what it rewrote. E5 cleans v2.12's text again
    (what uvlhub.io shows stays) and keeps B0's original beside it; E1 drops
    the schema it restored B0 in."""
    b1, b0 = hotfix_dumps
    params = isolated(
        "b0",
        dump=b1,
        b0=b0,
        b0_schema="iso_b0_b0",
        expected_head="f7a8b9c0d1e2",
        allow_open_conflicts=True,
        stages=("E0", "E1", "E3", "E4", "E5"),
    )
    report = run(params)
    facts = report["facts"]
    assert facts["b0"]["rows"] == len(synthetic.content_rows()[0])
    descriptions = facts["descriptions"]
    assert descriptions["originals"] == "b0"
    changed = [201, 202, 203, 204, 207, 208, 209, 210, 213, 214]
    assert descriptions["b0_differs"] == changed
    assert not any(alert.startswith("C-29") for alert in report["alerts"])
    with root_engine.connect() as connection:
        quarantined = {
            row.ds_meta_data_id: row
            for row in connection.exec_driver_sql(
                f"SELECT * FROM `{params.work_schema}`.quarantine_description"
            )
        }
        loaded = dict(
            connection.exec_driver_sql(
                f"SELECT id, description FROM `{params.target_schema}`.ds_meta_data"
            ).all()
        )
        left = connection.exec_driver_sql(
            "SELECT COUNT(*) FROM information_schema.schemata "
            "WHERE schema_name = 'iso_b0_b0'"
        ).scalar()
    assert sorted(quarantined) == changed
    assert quarantined[201].original == synthetic.description(1)
    assert quarantined[201].sanitized == loaded[201] == "<p>About dataset 1</p>alert(1)"
    assert loaded[205] == "<p>About dataset 5</p>" and 205 not in quarantined
    assert left == 0


# ── E4: identity ─────────────────────────────────────────────────────────


def test_e4_loads_the_accounts_but_the_seed_and_the_clashes(migrated):
    users = by_id(target(migrated, "user"))
    # 10 and 11 only differ in an emoji, which utf8mb4_unicode_ci took for
    # one and user.email's utf8mb4_bin does not; 16 and 17 in a space.
    assert sorted(users) == [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    assert dropped(migrated, "user") == {
        5: "seed",
        6: "seed",
        16: "held_by_conflict",
        17: "held_by_conflict",
    }
    clashes = {c for c in conflicts(migrated) if c[0].startswith("email_clash")}
    assert clashes == {("email_clash_canonical", "shared@uvlhub.test")}
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
    """C-28 with auth's must_reset_password: the hash is copied, and opens
    nothing but a reset link mailed to the owner."""
    users = by_id(target(migrated, "user"))
    jose = users[3]
    assert jose["email_verified_at"] is None
    assert jose["must_reset_password"] == 1
    assert jose["password"] == by_id(synthetic.users())[3]["password"]
    assert {i for i, u in users.items() if u["must_reset_password"]} == {3}
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
    assert usable == {1, 3, 4, 7, 9, 10, 11, 12, 13, 14, 15}


def test_e4_profiles_are_stripped_and_follow_their_account(migrated):
    profiles = by_id(target(migrated, "user_profile"))
    assert (
        profiles[101]["name"] == "Alice"
        and profiles[101]["affiliation"] == "Universidad de Sevilla"
    )
    assert dropped(migrated, "user_profile") == {
        105: "seed",
        106: "seed",
        116: "held_by_conflict",
        117: "held_by_conflict",
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
        9: "held_by_conflict",
    }
    # "GitHub " is github, written exactly; gitlab is no provider of uvlhub.
    assert identities[8]["provider"] == "github"
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
        ("identity_unknown_provider", "9"),
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


# ── E5: content ──────────────────────────────────────────────────────────


def test_e5_loads_the_datasets_with_the_state_their_metadata_implies(migrated):
    datasets = by_id(target(migrated, "datasets"))
    # 30, 31 and 32: the tombstones of 290, 292 and 293 (DM-4).
    assert sorted(datasets) == [1, 2, 3, 4, 5, 7, 8, 9, 10, 13, 14, 30, 31, 32]
    assert dropped(migrated, "datasets") == {
        6: "ghost_draft",
        11: "held_by_conflict",
        12: "seed",
    }
    state = {i: (d["status"], d["visibility"]) for i, d in datasets.items()}
    assert state[1] == ("published", "public")
    assert state[3] == ("sync_pending", "public")
    # Its deposition's record is somebody else's (C-09).
    assert state[4] == ("failed", "public")
    assert state[5] == ("draft", "public")
    assert state[7] == ("published", "anonymous")
    assert state[9] == ("published", "public")
    # §4.3: the day Zenodo published it, from its record; 7 has none
    # (doi_record_missing), so its created_at while that is open.
    assert datasets[1]["published_at"] == datetime(2026, 1, 25)
    assert datasets[3]["published_at"] == datetime(2025, 6, 1)
    assert datasets[7]["published_at"] == datasets[7]["created_at"]
    assert datasets[4]["published_at"] is None and datasets[5]["published_at"] is None
    assert migrated.report["facts"]["published_at"] == {
        "zenodo": 5,
        "created_at": [7, 8, 10],
    }
    assert datasets[4]["publisher_record_id"] == "1007"
    # The identifier as dataset0005 makes it neutral: a DOI is the pid, and
    # a DOI or a deposition is zenodo's.
    identifier = {
        i: (d["provider"], d["pid"], d["pid_scheme"]) for i, d in datasets.items()
    }
    assert identifier[1] == ("zenodo", "10.5281/zenodo.1001", "doi")
    assert identifier[3] == ("zenodo", "10.5281/zenodo.1005", "doi")
    assert identifier[4] == ("zenodo", None, None)
    assert identifier[5] == (None, None, None)
    assert all(d["publication_error"] is None for d in datasets.values())
    assert datasets[2]["dataset_origin_id"] == 1 and datasets[2]["dataset_version"] == 2
    assert {
        i: d["feature_model_count"] for i, d in datasets.items() if i in (1, 5, 13)
    } == {1: 2, 5: 2, 13: 3}


def test_e5_keeps_an_anonymous_datasets_authors_apart(migrated):
    meta = by_id(target(migrated, "ds_meta_data"))[207]
    assert json.loads(meta["private_authors"]) == [
        {
            "name": "Carol Danvers",
            "given_name": None,
            "family_name": None,
            "affiliation": "Kree",
            "orcid": synthetic.CAROL_ORCID,
            "user_id": 12,
        },
        {
            "name": "Hidden Two",
            "given_name": None,
            "family_name": None,
            "affiliation": None,
            "orcid": None,
            "user_id": None,
        },
    ]
    authors = by_id(target(migrated, "author"))
    # 7 is of a tombstone's metadata, whose citation names it.
    assert sorted(authors) == [1, 2, 3, 7]
    assert authors[1]["orcid"] == synthetic.ALICE_ORCID and authors[2]["orcid"] is None
    assert dropped(migrated, "author") == {6: "orphan", 8: "seed"}
    mapped = work(migrated, "id_map", "entity = 'author'")
    assert {m["source_id"] for m in mapped} == {4, 5, 9}


def test_e5_credits_each_author_as_dataset_0_9_0_does(migrated):
    """DL-5: the place from 0 in id order, the names apart only from
    "Family, Given", the account by the iD it signed in with; D18: no
    declaration, and nothing for orcid.org's cache."""
    authors = by_id(target(migrated, "author"))
    assert {
        i: (
            a["ds_meta_data_id"],
            a["position"],
            a["given_name"],
            a["family_name"],
            a["user_id"],
        )
        for i, a in authors.items()
    } == {
        # Alice's iD, written in lower case, is the one she signed in with.
        1: (201, 0, None, None, 1),
        2: (201, 1, "Bob", "Builder", None),
        # Two commas: not split.
        3: (202, 0, None, None, 1),
        7: (290, 0, None, None, None),
    }
    metas = target(migrated, "ds_meta_data")
    assert all(m["authors_declared_at"] is None for m in metas)
    assert all(m["authors_declared_by_id"] is None for m in metas)
    assert target(migrated, "dataset_orcid_check", order="orcid") == []


def test_e5_gives_each_dataset_its_public_id_root_and_concept(migrated):
    """CO-5, §4.2: a ULID of created_at whose random bits come from the
    key and the id, the same every run; DL-9: the root of the lineage as
    it loads; CT-4: the concept DOI as concept_pid."""
    from uvlhub_splent.migration_v2.content import public_id_of

    datasets = by_id(target(migrated, "datasets"))
    key = migrated.params.public_id_key
    assert all(
        d["public_id"] == public_id_of(key, i, d["created_at"])
        for i, d in datasets.items()
    )
    assert len({d["public_id"] for d in datasets.values()}) == len(datasets)
    assert (
        public_id_of("another key", 1, datasets[1]["created_at"])
        != (datasets[1]["public_id"])
    )
    # 14 stood on 1, as 2 does; its concept DOI puts it on 2 (C-05).
    assert {i: datasets[i]["lineage_root_id"] for i in (1, 2, 14, 5, 30)} == {
        1: 1,
        2: 1,
        14: 1,
        5: 5,
        30: 30,
    }
    assert {i for i, d in datasets.items() if d["concept_pid"]} == {
        1,
        2,
        3,
        9,
        14,
        32,
    }
    assert datasets[1]["concept_pid"] == synthetic.CONCEPT_DOI


def test_e5_takes_the_concept_doi_v2_12_did_not_keep_from_zenodo(migrated):
    """§4.3, CT-4: the records of datasets 3 and 9 in zenodo_snapshot give
    their concept DOIs, in concept_pid and in the metadata /doi/<concept>
    resolves by; a concept DOI v2.12 kept stays as it was."""
    datasets = by_id(target(migrated, "datasets"))
    metas = by_id(target(migrated, "ds_meta_data"))
    assert datasets[3]["concept_pid"] == synthetic.DATASET_3_CONCEPT
    assert (
        metas[datasets[3]["ds_meta_data_id"]]["dataset_concept_doi"]
        == synthetic.DATASET_3_CONCEPT
    )
    assert datasets[9]["concept_pid"] == "10.5281/zenodo.1010"
    assert datasets[1]["concept_pid"] == synthetic.CONCEPT_DOI
    assert migrated.report["facts"]["concepts_from_zenodo"] == [3, 9]


def test_e5_orphan_metadata_becomes_a_tombstone_or_goes(migrated):
    """DM-4: the metadata v2.12 left with a DOI when it deleted their
    dataset become withdrawn datasets, which dataset's landing answers with
    its tombstone, 293 with the DOI Zenodo minted, which v2.12 never saved
    (A15-04); the one without a DOI goes."""
    assert [
        (t["doi"], t["ds_meta_data_id"], t["dataset_id"])
        for t in sorted(work(migrated, "tombstone"), key=lambda t: t["doi"])
    ] == [
        (synthetic.ORPHAN_DOI, 290, 30),
        (synthetic.UNDATED_DOI, 292, 31),
        (synthetic.MINTED_DOI, 293, 32),
    ]
    reasons = dropped(migrated, "ds_meta_data")
    assert reasons[291] == "orphan" and reasons[212] == "seed"
    assert not {290, 292, 293} & set(reasons)
    datasets = by_id(target(migrated, "datasets"))
    for dataset_id, meta_id, doi in (
        (30, 290, synthetic.ORPHAN_DOI),
        (31, 292, synthetic.UNDATED_DOI),
        (32, 293, synthetic.MINTED_DOI),
    ):
        tombstone = datasets[dataset_id]
        assert tombstone["status"] == "withdrawn"
        assert tombstone["withdrawal_reason"] == "other"
        assert tombstone["withdrawal_note"].startswith("Deleted from uvlhub.io")
        assert tombstone["withdrawn_at"] is None
        assert (tombstone["ds_meta_data_id"], tombstone["pid"]) == (meta_id, doi)
        assert (tombstone["provider"], tombstone["pid_scheme"]) == ("zenodo", "doi")
        # Held by the administrator DM-13 names.
        assert tombstone["user_id"] == 1
    # The Zenodo snapshot dates 290's; nothing dates 292's, which is T0.
    assert datasets[30]["created_at"] == datetime(2025, 3, 1, 10, 0)
    assert datasets[30]["published_at"] == datetime(2025, 3, 2)
    assert (datasets[31]["created_at"], datasets[31]["published_at"]) == (T0, None)
    assert (datasets[32]["created_at"], datasets[32]["published_at"]) == (
        datetime(2025, 9, 10, 9, 30),
        datetime(2025, 9, 10),
    )
    assert datasets[32]["concept_pid"] == synthetic.MINTED_CONCEPT
    metas = by_id(target(migrated, "ds_meta_data"))
    assert metas[293]["dataset_doi"] == synthetic.MINTED_DOI
    assert migrated.report["facts"]["dois_minted_by_zenodo"] == {
        "datasets": [],
        "metadata_without_dataset": [293],
    }
    assert datasets[31]["visibility"] == "anonymous"
    hidden = by_id(target(migrated, "ds_meta_data"))[292]["private_authors"]
    assert json.loads(hidden) == [
        {
            "name": "Hidden Author",
            "given_name": None,
            "family_name": None,
            "affiliation": None,
            "orcid": None,
            "user_id": None,
        }
    ]
    found = conflicts(migrated)
    assert ("tombstone_undated", synthetic.UNDATED_DOI) in found
    assert ("tombstone_undated", synthetic.ORPHAN_DOI) not in found
    mapped = work(migrated, "id_map", "entity = 'tombstone'")
    assert {(m["source_id"], m["target_id"]) for m in mapped} == {
        (290, 30),
        (292, 31),
        (293, 32),
    }
    publisher = by_id(target(migrated, "ds_meta_data"))[204]["api_publisher_user_id"]
    assert publisher is None


LANDING = """
import json, sys
from splent_framework.utils.app_loader import get_create_app_in_testing_mode

app = get_create_app_in_testing_mode()
with app.test_client() as client:
    response = client.get(sys.argv[1], headers={"Accept": "application/json"})
    print(json.dumps({"status": response.status_code, "body": response.get_json(silent=True)}))
"""


def test_a_tombstones_doi_answers_410_with_its_citation(migrated):
    """What DM-4 is for, asked of dataset's own landing: the product's app,
    in a process of its own, on the rehearsal's uvlhub3."""
    env = child_env(
        migrated.params, HUBFILE_STORAGE_ROOT=str(migrated.params.store_root)
    )
    result = subprocess.run(
        [sys.executable, "-c", LANDING, f"/doi/{synthetic.ORPHAN_DOI}/"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    answer = json.loads(result.stdout.strip().splitlines()[-1])
    assert answer["status"] == 410
    body = answer["body"]
    assert body["error"] == "withdrawn" and body["doi"] == synthetic.ORPHAN_DOI
    assert body["reason"] == "other"
    # citation 0.2.0 writes the tombstone's citation, with the version and
    # the publisher between the title and the DOI.
    assert body["citation"].startswith(
        "Of a deleted dataset (2025). Deleted, with a DOI"
    )
    assert body["citation"].endswith(f"https://doi.org/{synthetic.ORPHAN_DOI}")


def test_e5_leaves_the_content_faults_open_as_conflicts(migrated):
    """What the plan resolves by hand (C-09, C-10, C-25, C-30) is open, for
    a decision; the branch of 1 is not, its concept DOI repaired it."""
    found = conflicts(migrated)
    assert ("doi_not_zenodo", "10.5072/zenodo.55") in found
    # Dataset 10 carries the DOI of dataset 9's deposition (C-30).
    assert ("doi_not_its_deposition", "10.5281/zenodo.1011") in found
    assert ("doi_repeated", "10.5281/zenodo.1011") in found
    # Dataset 7's DOI has no record at Zenodo (§4.3).
    assert ("doi_record_missing", "10.5281/zenodo.1009") in found
    # Dataset 4's deposition names somebody else's record (C-09).
    assert ("deposition_record_mismatch", "1007") in found
    assert ("checksum_unknown", "15") in found
    assert [ref for kind, ref in found if kind == "doi_record_missing"] == [
        "10.5281/zenodo.1009"
    ]
    assert not any(kind.startswith("lineage_") for kind, _ref in found)


def test_e5_repairs_a_lineage_by_its_concept_doi(migrated):
    """C-05: 2 and 14 both stood on 1; all three share a concept DOI, and in
    the order of their created_at their versions rise (1, 2, 3), so 14
    stands on 2, its version as it was. uvlhub_migration.curated says so."""
    datasets = by_id(target(migrated, "datasets"))
    assert [(i, datasets[i]["dataset_origin_id"]) for i in (1, 2, 14)] == [
        (1, None),
        (2, 1),
        (14, 2),
    ]
    assert datasets[14]["dataset_version"] == 3
    assert work(migrated, "curated") == [
        {
            "dataset_id": 14,
            "lineage": f"C-05 {synthetic.CONCEPT_DOI}",
            "old_origin_id": 1,
            "old_version": 3,
            "origin_id": 2,
            "version": 3,
        }
    ]
    assert migrated.report["facts"]["lineages_by_concept"] == {
        "repaired": [
            {"concept": synthetic.CONCEPT_DOI, "chain": [[1, None], [2, 1], [14, 2]]}
        ],
        "left": [],
    }


def test_e5_cleans_every_description_again_and_quarantines_the_originals(migrated):
    """C-01 (D21): html_legacy, cleaned by dataset's sanitiser; the
    original of each that changes in quarantine_description, with the
    plan's two classes in the report. The source is before the hotfix, so
    the originals are its own (C-29, test_e1_reads_b0_*)."""
    metas = by_id(target(migrated, "ds_meta_data"))
    assert {m["description_format"] for m in metas.values()} == {"html_legacy"}
    assert metas[201]["description"] == "<p>About dataset 1</p>"
    assert metas[202]["description"] == "<p>About dataset 2, in red</p>"
    assert metas[205]["description"] == "<p>About dataset 5</p>"
    quarantined = {
        q["ds_meta_data_id"]: q for q in work(migrated, "quarantine_description")
    }
    loaded_with_script = [201, 203, 204, 207, 208, 209, 210, 213, 214]
    assert sorted(quarantined) == sorted([202, *loaded_with_script])
    assert quarantined[201] == {
        "ds_meta_data_id": 201,
        "original": synthetic.description(1),
        "sanitized": "<p>About dataset 1</p>",
    }
    facts = migrated.report["facts"]["descriptions"]
    assert facts["originals"] == "source" and facts["b0_differs"] is None
    assert facts["active_content"] == loaded_with_script
    assert (facts["quarantined"], facts["formatting"]) == (10, 1)
    assert facts["elements"] == {"p": 11, "script": 9, "span": 1}


def test_e5_makes_the_publication_doi_bare_and_says_each_tag_once(migrated):
    """C-16 and C-23 (the tags a string, as decided)."""
    metas = by_id(target(migrated, "ds_meta_data"))
    assert metas[201]["publication_doi"] == "10.1000/paper1"
    assert metas[202]["publication_doi"] == "https://example.org/paper2"
    assert metas[209]["publication_doi"] == "in press"
    assert metas[205]["publication_doi"] is None
    assert metas[201]["tags"] == "uvl,models" and metas[203]["tags"] == "uvl,models"
    assert metas[290]["tags"] is None
    notes = migrated.report["notes"]
    assert notes["ds_meta_data: publication_doi normalised (C-16)"] == 7
    assert (
        notes[
            "ds_meta_data: publication_doi neither a DOI nor an address, kept as it is (C-16)"
        ]
        == 1
    )


def test_e5_files_and_feature_models(migrated):
    files = by_id(target(migrated, "hubfiles"))
    assert dropped(migrated, "hubfiles") == {11: "held_by_conflict", 12: "seed"}
    assert files[3]["checksum_algo"] == "md5" and files[1]["checksum_algo"] == "sha256"
    assert files[15]["checksum_algo"] is None
    assert {f["artifact_type"] for f in files.values()} == {"uvl"}
    models = by_id(target(migrated, "feature_model"))
    assert models[66]["dataset_id"] == 5  # its file's dataset (C-07)
    # E5 copies v2.12's metrics of the files it loads, legacy until E9
    # makes them again (§7.3, test_derived).
    copied = {c["entity"]: c for c in work(migrated, "counts")}["hubfile_metrics"]
    assert (copied["source"], copied["target"]) == (2, 1)
    assert dropped(migrated, "hubfile_metrics") == {12: "hubfile_not_loaded"}
    assert (
        migrated.report["notes"][
            "hubfile_metrics: v2.12's, legacy until extracted again (§7.3)"
        ]
        == 1
    )


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


def test_e7_checks_pass_and_what_keeps_the_cutover_off(migrated):
    checks = {c["name"]: c for c in migrated.report["checks"]}
    failing = {name for name, c in checks.items() if not c["ok"]}
    # V-08 holds: dataset 3's file in mismatch comes back from Zenodo (§6.2
    # step 5); V-09: the concept DOI repaired the branch of dataset 1;
    # E9-reindex: the rehearsal has no search node (test_derived).
    assert failing == {"E9-reindex"}
    for name in (
        "V-01",
        "V-02",
        "V-03",
        "V-04",
        "V-05",
        "V-06",
        "V-07",
        "V-09",
        "V-10",
        "V-11",
        "V-13",
        "V-15",
        "V-16",
        "empty-tables",
    ):
        assert checks[name]["ok"] and checks[name]["blocking"], name
    assert {name for name, c in checks.items() if not c["blocking"]} == {
        "E9-factlabel",
        "E9-formats",
        "E9-reindex",
    }
    # What keeps it off: the conflicts left open, and DM-1.
    assert migrated.report["conflicts"]
    # Nothing in the tests says what v2.12's key was (DM-1).
    assert migrated.report["dm1"] == {"rotation_checked": False}
    assert migrated.report["ready_for_cutover"] is False


# ── E8: files ────────────────────────────────────────────────────────────


def test_e8_links_every_file_to_its_key_and_says_what_it_found(migrated):
    store = migrated.params.store_root
    files = by_id(target(migrated, "hubfiles"))
    status = {i: f["storage_status"] for i, f in files.items()}
    assert (
        status[4] == "recovered"
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


def test_dm10_gives_a_second_file_on_one_path_a_name_of_its_own(migrated):
    """C-11: 13 and 14 are dataset 13's dup.uvl. 13, the one v2.12 served,
    keeps the name; 14 is renamed once E8 has linked it by its old one, and
    hubfile's hubfile_alias keeps that, so its /hubfiles/raw URL answers a
    308 to the new name."""
    files = by_id(target(migrated, "hubfiles"))
    assert (files[13]["name"], files[14]["name"]) == ("dup.uvl", "dup~14.uvl")
    assert files[14]["storage_status"] == "ok"
    assert files[14]["storage_key"] == "datasets/13/src/14"
    assert [
        (a["hubfile_id"], a["directory_path"], a["name"], a["created_at"])
        for a in target(migrated, "hubfile_alias")
    ] == [(14, "", "dup.uvl", T0)]
    assert not any(c[0] == "duplicate_path" for c in conflicts(migrated))
    checks = {c["name"]: c for c in migrated.report["checks"]}
    assert checks["unique-paths"]["ok"]


def test_e8_writes_the_manifest_with_what_no_row_names(migrated):
    manifest = work(migrated, "file_manifest")
    loose = {m["path"]: m["status"] for m in manifest if m["hubfile_id"] is None}
    assert loose == {
        "temp/1/half.uvl": "temp",
        "user_1/dataset_1/glencoe/model one.json": "derived",
        "user_1/dataset_99/uvl/lost.uvl": "orphan",
        "user_2/dataset_3/glencoe/drift.json": "derived",
        "user_17/dataset_11/uvl/held.uvl": "orphan",
        "user_5/dataset_12/uvl/file1.uvl": "orphan",
    }
    rows_ = {m["hubfile_id"]: m for m in manifest if m["hubfile_id"]}
    assert rows_[2]["path"] == "user_1/dataset_1/uvl/sub dir/a#b/b#2.uvl"
    assert rows_[6]["status"] == "missing"
    assert rows_[4]["status"] == "recovered"
    # Dataset 5 is a draft: its missing file is no conflict (§6.2 step 6).
    assert not any(kind.startswith("file_") for kind, _ref in conflicts(migrated))


def test_e8_recovers_a_published_file_with_zenodos_bytes(migrated):
    """§6.2 step 5: file 4 of published dataset 3 is in the mirror with
    other bytes than its row says; Zenodo's are the row's. They go to its
    key as a new file, so the mirror keeps its own, the row says
    recovered, what uvl derived from the mirror's bytes goes, the mirror's
    bytes stay beside it as the file's readable copy, and file_repair keeps
    what the row and the mirror had."""
    store = migrated.params.store_root
    row = by_id(target(migrated, "hubfiles"))[4]
    content = synthetic.content_of(4)
    stored = store / row["storage_key"]
    mirror = store / ".legacy_mirror" / "user_2" / "dataset_3" / "uvl" / "drift.uvl"
    assert stored.read_bytes() == content
    assert stored.stat().st_nlink == 1
    assert mirror.read_bytes() == content + b"// edited after it was uploaded\n"
    assert (row["size"], row["checksum"], row["checksum_algo"]) == (
        len(content),
        synthetic.sha256(content),
        "sha256",
    )
    assert row["content_sha256"] == synthetic.sha256(content)
    derived = store / "datasets" / "3" / "derived" / "4" / "glencoe"
    assert not derived.exists() or derived.read_bytes() != b"{}"
    readable = store / "datasets" / "3" / "derived" / "4" / "readable"
    assert readable.read_bytes() == mirror.read_bytes()

    (repair,) = work(migrated, "file_repair")
    assert repair == {
        "hubfile_id": 4,
        "dataset_id": 3,
        "deposition_id": 1005,
        "outcome": "replaced",
        "origin": "file",
        "zenodo_key": "drift.uvl",
        "zip_entry": None,
        "old_status": "mismatch",
        "old_size": len(content),
        "old_checksum": synthetic.sha256(content),
        "old_checksum_algo": "sha256",
        "mirror_size": mirror.stat().st_size,
        "mirror_sha256": synthetic.sha256(mirror.read_bytes()),
        "size": len(content),
        "checksum": synthetic.sha256(content),
        "checksum_algo": "sha256",
        "content_sha256": synthetic.sha256(content),
    }
    assert migrated.report["facts"]["zenodo_repair"] == {
        "recovered": 1,
        "by_origin": {"file": 1},
        "by_outcome": {"replaced": 1},
        "rows_changed": 0,
        "readable_copies_kept": 1,
        "not_recovered": [],
    }


# ── The cutover's run, and a second one ──────────────────────────────────


def test_e3_refuses_a_schema_that_is_not_the_contracts(
    isolated, synthetic_dump, seedless
):
    """V-12 and V-14 on a real uvlhub3: a contract that expects another head
    and another collation than the pinned features give stops E3."""
    contract = contract_module.load()
    user = contract.tables["user"]
    # As if auth went back to the table's collation for the address.
    email = replace(user.columns["email"], collation="utf8mb4_unicode_ci")
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
        "V-14 user.email: utf8mb4_bin, the contract says utf8mb4_unicode_ci",
        "user.email: collation utf8mb4_bin, the contract says utf8mb4_unicode_ci",
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
    # E9 has filled hubfile_factlabel since E7 found it empty.
    filled.pop("hubfile_factlabel")
    assert filled == {"auth_token": 1}


def test_v16_finds_a_signed_value_carried_over(migrated):
    """DM-1: a reset link of v2.12 copied into any text column that loads
    is something the rotated key would leave behind; V-16 names it."""
    from types import SimpleNamespace

    from uvlhub_splent.migration_v2.verify import v16_nothing_signed

    ctx = SimpleNamespace(contract=contract_module.load(), params=migrated.params)
    link = synthetic.reset_link("alice@uvlhub.test")
    schema = migrated.params.target_schema
    with migrated.engine.connect() as connection:
        assert v16_nothing_signed(ctx, connection).ok
        connection.execute(
            sa.text(
                f"UPDATE `{schema}`.user_profile SET affiliation = :link WHERE id = 101"
            ),
            {"link": link},
        )
        check = v16_nothing_signed(ctx, connection)
        connection.rollback()
    assert not check.ok and check.blocking
    assert check.detail == {
        "copied_from_signed": [],
        "tokens": {},
        "signed_values": {"user_profile.affiliation": 1},
    }


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
    assert "1 open conflict(s) of kind email_clash_canonical" in refusal.value.reasons
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
    tables = [
        t.name
        for t in contract_module.load().by_role(contract_module.LOAD)
        if t.name not in REWRITTEN
    ]
    before = _digest(migrated, tables)
    with pytest.raises(Refused) as refusal:
        run(migrated.params)
    assert refusal.value.stage == "E0"
    assert any("migration.completed" in reason for reason in refusal.value.reasons)

    b2 = tmp_path / "b2.sql"
    b2.write_text("-- B2, taken just now\n")
    run(replace(migrated.params, force=True, b2=b2))
    assert _digest(migrated, tables) == before


def test_e8_empties_only_what_hubfile_keeps(tmp_path):
    from uvlhub_splent.migration_v2.files import empty_store

    mirror = tmp_path / ".legacy_mirror"
    (mirror / "user_1").mkdir(parents=True)
    (tmp_path / "datasets" / "1" / "src").mkdir(parents=True)
    (tmp_path / "trash").mkdir()
    empty_store(tmp_path, mirror)
    assert sorted(p.name for p in tmp_path.iterdir()) == [".legacy_mirror"]
    assert (mirror / "user_1").is_dir()

    (tmp_path / "datasets").mkdir()
    (tmp_path / "user_1").mkdir()
    with pytest.raises(Refused) as refusal:
        empty_store(tmp_path, mirror)
    assert "holds user_1" in refusal.value.reasons[0]
    assert (tmp_path / "datasets").is_dir()
