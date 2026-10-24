"""``python -m uvlhub_splent.migration_v2``: the commands, without a server.

What reaches a database is test_pipeline's; these check what the commands
say and refuse before they connect.
"""

from __future__ import annotations

import json
import subprocess
import sys

from click.testing import CliRunner

from uvlhub_splent.migration_v2.cli import REFUSED, main

RUN = ["--db-host", "nowhere", "--t0", "2026-11-20T00:00:00"]


def test_the_module_runs_as_a_command():
    result = subprocess.run(
        [sys.executable, "-m", "uvlhub_splent.migration_v2", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    for command in ("run", "preflight", "grants", "contract"):
        assert command in result.stdout


def test_grants_make_an_account_for_the_four_schemas_only():
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
