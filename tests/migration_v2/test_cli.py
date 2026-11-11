"""``python -m uvlhub_splent.migration_v2``: the commands, without a server.

What reaches a database is test_pipeline's; these check what the commands
say and refuse before they connect.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest
from click.testing import CliRunner

from uvlhub_splent.migration_v2.cli import REFUSED, main

from .conftest import needs_pins

RUN = ["--db-host", "nowhere", "--t0", "2026-11-20T00:00:00"]


def test_the_module_runs_as_a_command():
    result = subprocess.run(
        [sys.executable, "-m", "uvlhub_splent.migration_v2", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    for command in (
        "run",
        "preflight",
        "grants",
        "contract",
        "zenodo-snapshot",
        "zenodo-files",
    ):
        assert command in result.stdout


def test_grants_make_an_account_for_the_five_schemas_only():
    result = CliRunner().invoke(main, ["grants"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines[0].startswith("-- MIGRATION_DB_PASSWORD=")
    assert lines[1].startswith("CREATE USER 'migrator'@'%' IDENTIFIED BY ")
    assert lines[2:] == [
        f"GRANT ALL PRIVILEGES ON `{schema}`.* TO 'migrator'@'%';"
        for schema in (
            "uvlhub3",
            "uvlhub_v2_src",
            "uvlhub_v2_ref",
            "uvlhub_migration",
            "uvlhub_migration_inputs",
        )
    ]


def test_contract_says_what_it_holds():
    result = CliRunner().invoke(main, ["contract"])
    assert result.exit_code == 0
    summary = json.loads(result.output)
    assert summary["database"] == "utf8mb4 utf8mb4_unicode_ci"
    assert "user" in summary["tables"]["load"]


@needs_pins
def test_the_installed_features_are_the_contracts():
    summary = json.loads(CliRunner().invoke(main, ["contract"]).output)
    assert summary["versions"] == []


def test_preflight_refuses_what_it_cannot_keep_before_it_connects(monkeypatch):
    monkeypatch.setenv("RUN_DB_SEED", "false")
    result = CliRunner().invoke(main, ["preflight", *RUN, "--expected-head", "001"])
    assert result.exit_code == REFUSED
    assert "E0 refused:" in result.output
    assert "MIGRATION_EXPECTED_HEAD '001' is not a head of v2.12" in result.output


def test_an_unknown_stage_is_a_usage_error():
    result = CliRunner().invoke(
        main, ["run", *RUN, "--expected-head", "e5f6a7b8c9d0", "--stages", "E0,E42"]
    )
    assert result.exit_code == 2
    assert "no such stage: E42" in result.output


def test_unknown_derived_data_is_a_usage_error():
    result = CliRunner().invoke(
        main, ["run", *RUN, "--expected-head", "e5f6a7b8c9d0", "--derived", "index"]
    )
    assert result.exit_code == 2
    assert "no such derived data: index" in result.output


def test_the_features_processes_reach_the_migrators_server(monkeypatch):
    """E3 and E8 run the features' commands with the server, the port
    (MARIADB_PORT, splent_framework 1.24.0), the account and uvlhub3 of the
    run, and never a seed, whatever the product's .env says."""
    from uvlhub_splent.migration_v2.params import Params, Server, parse_t0
    from uvlhub_splent.migration_v2.schema import child_env

    monkeypatch.setenv("MARIADB_HOSTNAME", "uvlhub_splent_db")
    monkeypatch.setenv("RUN_DB_SEED", "true")
    params = Params(
        server=Server(host="cutover-db", port=3407, user="migrator", password="pw"),
        t0=parse_t0("2026-11-20T00:00:00"),
        expected_head="e5f6a7b8c9d0",
    )
    env = child_env(params, HUBFILE_STORAGE_ROOT="/store")
    assert {
        key: env[key]
        for key in (
            "MARIADB_HOSTNAME",
            "MARIADB_PORT",
            "MARIADB_DATABASE",
            "MARIADB_TEST_DATABASE",
            "MARIADB_USER",
            "MARIADB_PASSWORD",
            "RUN_DB_SEED",
            "HUBFILE_STORAGE_ROOT",
        )
    } == {
        "MARIADB_HOSTNAME": "cutover-db",
        "MARIADB_PORT": "3407",
        "MARIADB_DATABASE": "uvlhub3",
        "MARIADB_TEST_DATABASE": "uvlhub3",
        "MARIADB_USER": "migrator",
        "MARIADB_PASSWORD": "pw",
        "RUN_DB_SEED": "false",
        "HUBFILE_STORAGE_ROOT": "/store",
    }


# ── splent product:migrate-v2 ────────────────────────────────────────────


@pytest.fixture
def app_with_a_pool(tmp_path):
    """An app whose engine keeps a pooled connection, as the app the CLI
    builds for a product command may."""
    from flask import Flask
    from splent_framework.db import db

    app = Flask("migrate-v2")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path / 'app.db'}"
    db.init_app(app)
    with app.app_context():
        with db.engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        assert db.engine.pool.checkedin() == 1
        yield db


def test_the_product_command_is_the_migrators(app_with_a_pool):
    from uvlhub_splent.commands import cli_commands, migrate_v2

    assert cli_commands == [migrate_v2]
    assert set(migrate_v2.commands) == {
        "run",
        "preflight",
        "grants",
        "contract",
        "zenodo-snapshot",
        "zenodo-files",
    }


def test_the_product_command_lets_the_apps_connections_go_before_e0(
    app_with_a_pool, monkeypatch
):
    from uvlhub_splent.commands import migrate_v2

    monkeypatch.setenv("RUN_DB_SEED", "false")
    result = CliRunner().invoke(
        migrate_v2, ["preflight", *RUN, "--expected-head", "001"]
    )
    assert result.exit_code == REFUSED
    assert app_with_a_pool.engine.pool.checkedin() == 0


def test_the_product_command_refuses_while_the_app_holds_a_connection(
    app_with_a_pool,
):
    from uvlhub_splent.commands import migrate_v2

    with app_with_a_pool.engine.connect():
        result = CliRunner().invoke(migrate_v2, ["grants"])
    assert result.exit_code == 1
    assert "the app holds 1 connection(s)" in result.output
    assert "MIGRATION_DB_PASSWORD" not in result.output


def test_a_curation_that_does_not_hold_is_a_usage_error(tmp_path):
    bad = tmp_path / "curation.toml"
    bad.write_text("version = 2\n")
    result = CliRunner().invoke(
        main,
        ["run", *RUN, "--expected-head", "e5f6a7b8c9d0", "--curation", str(bad)],
    )
    assert result.exit_code == 2
    assert "version 1 is the one this migrator reads" in result.output


def test_the_curation_is_r1s_unless_told_otherwise():
    from uvlhub_splent.migration_v2 import curation
    from uvlhub_splent.migration_v2.cli import _curation

    assert _curation(None) == curation.CURATION
    assert _curation("none") is None
