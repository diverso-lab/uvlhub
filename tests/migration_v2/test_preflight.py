"""E0: every safeguard of §3.4 refuses, and a clean server passes.

Each test works on schemas of its own (isolated), so none of them touches
the rehearsal the other tests read.
"""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import replace

import pytest
import sqlalchemy as sa

from uvlhub.migration_v2 import contract as contract_module
from uvlhub.migration_v2.params import Refused
from uvlhub.migration_v2.pipeline import Context
from uvlhub.migration_v2.preflight import LOCK_NAME, preflight, release_lock

from . import synthetic


def run_e0(params, contract=None):
    """E0 alone; the reasons it refuses with, [] when it lets the run go."""
    ctx = Context(params, contract)
    try:
        preflight(ctx)
        return []
    except Refused as refusal:
        assert refusal.stage == "E0"
        return refusal.reasons
    finally:
        ctx.close()


def execute(engine, *statements, **params):
    with engine.connect() as connection:
        for statement in statements:
            connection.execute(sa.text(statement), params)
        connection.commit()


@pytest.fixture
def params(isolated, seedless):
    return isolated("e0")


def test_a_lock_on_a_server_that_went_away_is_given_back_quietly():
    """R1: the server was killed mid-run, and RELEASE_LOCK's error, raised
    from the run's last finally, hid the crash the run stopped on."""

    class Dropped:
        closed = False

        def execute(self, *_args, **_kwargs):
            raise sa.exc.OperationalError(
                "SELECT RELEASE_LOCK", {}, Exception("Lost connection")
            )

        def commit(self):
            raise AssertionError("nothing to commit on a dropped connection")

        def close(self):
            self.closed = True

    dropped = Dropped()
    release_lock(dropped)
    assert dropped.closed


def test_a_clean_server_lets_the_run_go(params):
    assert run_e0(params) == []


def test_it_refuses_unless_nothing_seeds(params, monkeypatch):
    monkeypatch.setenv("RUN_DB_SEED", "true")
    assert run_e0(params) == [
        "RUN_DB_SEED is not false: nothing the migrator starts may seed uvlhub3"
    ]
    monkeypatch.delenv("RUN_DB_SEED")
    assert len(run_e0(params)) == 1


def test_it_refuses_while_another_run_holds_the_lock(params, server):
    from uvlhub.migration_v2.db import make_engine

    engine = make_engine(server.host, 3306, "migrator", server.migrator_password)
    with engine.connect() as other:
        assert (
            other.execute(sa.text("SELECT GET_LOCK(:n, 0)"), {"n": LOCK_NAME}).scalar()
            == 1
        )
        reasons = run_e0(params)
        other.execute(sa.text("SELECT RELEASE_LOCK(:n)"), {"n": LOCK_NAME})
    engine.dispose()
    assert reasons == [f"GET_LOCK('{LOCK_NAME}', 0) is held: another run is on"]


def test_it_refuses_while_anyone_else_is_connected(params, server, root_engine):
    from uvlhub.migration_v2.db import make_engine

    execute(
        root_engine,
        "DROP USER IF EXISTS 'webapp'@'%'",
        "CREATE USER 'webapp'@'%' IDENTIFIED BY 'webapp'",
    )
    engine = make_engine(server.host, 3306, "webapp", "webapp")
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
            reasons = run_e0(params)
    finally:
        engine.dispose()
        execute(root_engine, "DROP USER 'webapp'@'%'")
    assert len(reasons) == 1
    assert reasons[0].startswith("a connection that is not the migrator's: webapp@")


@pytest.fixture
def opened(params, root_engine):
    """A uvlhub3 with the tables E0 reads, empty."""
    target, work = params.target_schema, params.work_schema
    execute(
        root_engine,
        f"CREATE DATABASE `{target}`",
        f"CREATE TABLE `{target}`.datasets (id INT PRIMARY KEY, created_at DATETIME NOT NULL)",
        f"CREATE TABLE `{target}`.mail_outbox (id INT PRIMARY KEY, state VARCHAR(16), "
        "created_at DATETIME, sent_at DATETIME)",
        f"CREATE TABLE `{target}`.`user` (id INT PRIMARY KEY, last_login_at DATETIME)",
        f"CREATE TABLE `{target}`.auth_token (id INT PRIMARY KEY)",
        f"CREATE DATABASE `{work}`",
        f"CREATE TABLE `{work}`.run (id INT PRIMARY KEY, completed_at DATETIME)",
    )
    assert run_e0(params) == []
    return params


@pytest.mark.parametrize(
    "statement, reason",
    [
        (
            "INSERT INTO `{target}`.datasets VALUES (1, :after)",
            "1 row(s) of datasets created after T0",
        ),
        (
            "INSERT INTO `{target}`.mail_outbox VALUES (1, 'sent', :before, :after)",
            "1 mail(s) sent from the outbox",
        ),
        ("INSERT INTO `{target}`.`user` VALUES (1, :after)", "1 account(s) signed in"),
        (
            "INSERT INTO `{target}`.auth_token VALUES (1)",
            "1 row(s) in auth_token, which the migration leaves empty",
        ),
        (
            "INSERT INTO `{work}`.run VALUES (1, '2026-11-20 03:00:00')",
            "a run completed at 2026-11-20 03:00:00 (migration.completed): 3.0 may have opened since",
        ),
    ],
)
def test_it_refuses_a_uvlhub3_that_has_been_used(
    opened, root_engine, statement, reason
):
    execute(
        root_engine,
        statement.format(target=opened.target_schema, work=opened.work_schema),
        after=synthetic.T0.replace(hour=5),
        before=synthetic.T0,
    )
    assert run_e0(opened) == [reason]


def test_force_needs_a_b2_of_the_last_15_minutes(opened, root_engine, tmp_path):
    execute(
        root_engine,
        f"INSERT INTO `{opened.target_schema}`.datasets VALUES (1, :after)",
        after=synthetic.T0.replace(hour=5),
    )
    used = "1 row(s) of datasets created after T0"
    needs = "--force needs --b2 with a B2 taken in the last 15 minutes"
    assert run_e0(replace(opened, force=True)) == [used, needs]

    b2 = tmp_path / "b2.sql"
    b2.write_text("-- B2\n")
    stale = time.time() - 16 * 60
    os.utime(b2, (stale, stale))
    assert run_e0(replace(opened, force=True, b2=b2)) == [used, needs]

    os.utime(b2, None)
    assert run_e0(replace(opened, force=True, b2=b2)) == []


def test_it_refuses_parameters_it_cannot_keep_its_word_with(params):
    assert run_e0(replace(params, expected_head="001")) == [
        "MIGRATION_EXPECTED_HEAD '001' is not a head of v2.12 (e5f6a7b8c9d0, f7a8b9c0d1e2)"
    ]
    assert run_e0(replace(params, ttl_read_days=400)) == [
        "a token life of 400 days: apikeys gives 1 to 365"
    ]
    assert run_e0(replace(params, public_id_key="")) == [
        "neither MIGRATION_PUBLIC_ID_KEY nor SECRET_KEY is set: E5 derives the "
        "public id of every dataset from it (CO-5, §4.2)"
    ]
    assert run_e0(replace(params, mail_from="")) == [
        "MAIL_FROM is not an address: the notices E6 holds in mail's outbox go "
        "from the one 3.0 sends from"
    ]
    assert run_e0(replace(params, hold_tag="rb 2")) == [
        "--hold-tag 'rb 2' names no batch of mail's: 1 to 64 letters, digits, "
        "'.', '_' or '-'"
    ]


def test_it_refuses_features_the_contract_was_not_written_for(params):
    contract = contract_module.load()
    # A version no release will have, whatever the product pins.
    features = dict(
        contract.features, splent_feature_dataset={"version": "9.9.9", "head": "x"}
    )
    installed = contract_module.installed_version("splent_feature_dataset")
    assert run_e0(params, replace(contract, features=features)) == [
        f"splent_feature_dataset is {installed}, the contract was written for 9.9.9"
    ]


# ── DM-1 ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "secret_key, v2_key, refused, checked",
    [
        ("a new key of 3.0, long enough to sign", None, None, False),
        ("a new key of 3.0, long enough to sign", "the key of v2.12", None, True),
        ("the key of v2.12", "the key of v2.12", "is v2.12's", False),
        (None, "the key of v2.12", "SECRET_KEY is not", False),
    ],
)
def test_e0_refuses_the_secret_key_of_v2_12(
    monkeypatch, secret_key, v2_key, refused, checked
):
    """DM-1: E0 holds SECRET_KEY to the sha256 of v2.12's, never the key."""
    from types import SimpleNamespace

    from uvlhub.migration_v2.preflight import secret_key_rotated

    for name, value in (
        ("SECRET_KEY", secret_key),
        (
            "MIGRATION_V2_SECRET_KEY_SHA256",
            v2_key and hashlib.sha256(v2_key.encode()).hexdigest().upper(),
        ),
    ):
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    ctx = SimpleNamespace(facts={})
    reasons = secret_key_rotated(ctx)
    if refused is None:
        assert reasons == []
    else:
        assert len(reasons) == 1 and refused in reasons[0]
    assert ctx.facts["dm1"] == {"rotation_checked": checked}
