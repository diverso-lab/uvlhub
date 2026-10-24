"""The DDL of v2.12 the tests start from is the monolith's chain's (R0)."""

from __future__ import annotations

import pytest

from . import v2_schema


def test_the_chain_goes_from_the_first_revision_to_the_release():
    if not v2_schema.MONOLITH_VERSIONS.is_dir():
        pytest.skip(
            "the monolith is not in this workspace (_reference/uvlhub_monolith)"
        )
    scripts = [script.name.split("_")[0] for script in v2_schema.chain()]
    assert scripts[0] == "84bec63cef2e" and scripts[-1] == v2_schema.HEAD
    # Every revision but the hotfix's, the merge of the two branches included.
    assert len(scripts) == 19 and "69b397b5322b" in scripts


def test_the_vendored_ddl_is_the_monolith_chains(server):
    """Run the chain again on the throwaway server and compare: a change in
    the monolith's migrations, or in how MariaDB writes them, shows here."""
    if not v2_schema.MONOLITH_VERSIONS.is_dir():
        pytest.skip(
            "the monolith is not in this workspace (_reference/uvlhub_monolith)"
        )
    built = v2_schema.build_ddl(server.host, server.root_password, schema="iso_v2ref")
    assert built == v2_schema.VENDORED.read_text(encoding="utf-8")
    # Read only: nothing was compiled into the monolith's folder.
    assert not (v2_schema.MONOLITH_VERSIONS / "__pycache__").exists()
