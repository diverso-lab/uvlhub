"""MIG-03: contract.toml against the schema the pinned features create.

The rehearsal's E3 builds uvlhub3 with the product's own db:upgrade, so
these read the schema of exactly the features the product pins. A pin that
changes a table the migration fills, adds one, or moves a head fails here
first, and the contract and the migrator change in the same commit.
"""

from __future__ import annotations

import tomllib
from dataclasses import replace
from pathlib import Path

import pytest
import sqlalchemy as sa

from uvlhub_splent.migration_v2 import contract as contract_module

from .conftest import needs_pins

PRODUCT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def contract():
    return contract_module.load()


def _columns(migrated, schema):
    with migrated.engine.connect() as connection:
        return contract_module.schema_columns(connection, schema)


def test_uvlhub3_is_what_the_contract_says(migrated, contract):
    """Tables, columns, types, nullability and collations: no difference."""
    assert (
        contract_module.differences(
            contract, _columns(migrated, migrated.params.target_schema)
        )
        == []
    )


def test_uvlhub3_defaults_to_the_contracts_collation(migrated, contract):
    with migrated.engine.connect() as connection:
        default = connection.execute(
            sa.text(
                "SELECT default_character_set_name, default_collation_name "
                "FROM information_schema.schemata WHERE schema_name = :s"
            ),
            {"s": migrated.params.target_schema},
        ).one()
    assert (
        tuple(default)
        == (contract.charset, contract.collation)
        == ("utf8mb4", "utf8mb4_unicode_ci")
    )


def test_v14_reads_the_contract_from_the_inputs_schema(migrated, contract):
    from uvlhub_splent.migration_v2.schema import V14

    with migrated.engine.connect() as connection:
        copied = connection.execute(
            sa.text(
                f"SELECT COUNT(*) FROM `{migrated.params.inputs_schema}`.contract_collation"
            )
        ).scalar()
        different = connection.execute(
            sa.text(V14.format(inputs=f"`{migrated.params.inputs_schema}`")),
            {"target": migrated.params.target_schema},
        ).all()
    assert copied == len(contract.collations())
    assert different == []


@needs_pins
def test_the_contract_is_written_for_the_pinned_features(contract):
    """Every feature of the product that has migrations is in [features].
    Its head, not its version, is held to what the product pins (below)."""
    pins = tomllib.loads((PRODUCT / "pyproject.toml").read_text())["tool"]["splent"]
    pinned = {}
    for entry in pins["features"] + pins.get("features_prod", []):
        name, _, version = entry.split("/")[-1].partition("@")
        pinned[name] = version.lstrip("v")
    features = PRODUCT / "features" / "splent_io"
    with_migrations = {
        name
        for name, version in pinned.items()
        if list(
            features.glob(
                f"{name}@v{version}/src/splent_io/{name}/migrations/versions/*.py"
            )
        )
    }
    assert set(contract.features) == with_migrations


@needs_pins
def test_each_head_is_the_last_revision_of_its_feature(contract):
    """At the version the product pins, whatever version the contract was
    written with: a release that adds no migration keeps the head."""
    pins = tomllib.loads((PRODUCT / "pyproject.toml").read_text())["tool"]["splent"]
    pinned = {}
    for entry in pins["features"] + pins.get("features_prod", []):
        name, _, version = entry.split("/")[-1].partition("@")
        pinned[name] = version.lstrip("v")
    for name, entry in contract.features.items():
        folder = next(
            (PRODUCT / "features" / "splent_io").glob(
                f"{name}@v{pinned[name]}/src/splent_io/{name}/migrations/versions"
            )
        )
        assert contract_module.migration_heads(folder) == {entry["head"]}, name


def test_every_column_loaded_says_where_it_comes_from(contract):
    for table in contract.by_role(contract_module.LOAD):
        for column in table.columns.values():
            assert column.source or column.rule, f"{table.name}.{column.name}"


def test_every_source_is_a_column_of_v2_12(migrated, contract):
    source = _columns(migrated, migrated.params.source_schema)
    for table in contract.by_role(contract_module.LOAD):
        for column in table.columns.values():
            if column.source:
                origin, _, name = column.source.partition(".")
                assert name in source.get(origin, {}), (
                    f"{table.name}.{column.name}: {column.source}"
                )


def test_every_null_the_target_refuses_has_a_rule(migrated, contract):
    """C-27: a column NULL may come from (v2.12 admits it) and the target
    refuses says what is written instead."""
    source = _columns(migrated, migrated.params.source_schema)
    for table in contract.by_role(contract_module.LOAD):
        for column in table.columns.values():
            if not column.source or column.nullable:
                continue
            origin, _, name = column.source.partition(".")
            if source[origin][name]["nullable"]:
                assert column.on_null, (
                    f"{table.name}.{column.name} from nullable {column.source}"
                )


def test_the_report_lists_what_dm15_still_asks(migrated, contract):
    pending = migrated.report["dm15_pending"]
    assert pending == contract.dm15_pending()
    # auth 1.27.0, identities 0.5.0 and dataset (concept_pid, and pid since
    # dataset0012) compare the identifiers exactly; what is left is the
    # tags, which have no column yet.
    assert pending == [
        "dataset_tag.name (C-23: tags stay a string in ds_meta_data.tags): "
        "no such column yet",
    ]


def test_a_drift_is_named(contract):
    columns = {
        name: {
            column.name: {
                "type": column.type,
                "nullable": column.nullable,
                "collation": column.collation,
            }
            for column in table.columns.values()
        }
        for name, table in contract.tables.items()
    }
    assert contract_module.differences(contract, columns) == []
    columns["user"]["email"]["collation"] = "utf8mb4_unicode_ci"
    columns["user"]["role"]["nullable"] = True
    columns["hubfiles"]["name"]["type"] = "varchar(255)"
    columns["datasets"]["concept_doi"] = {
        "type": "varchar(255)",
        "nullable": True,
        "collation": "utf8mb4_bin",
    }
    columns["dataset_tag"] = {
        "name": {"type": "varchar(64)", "nullable": False, "collation": "utf8mb4_bin"}
    }
    del columns["api_token"]["prefix"]
    found = contract_module.differences(contract, columns)
    assert found == [
        "dataset_tag: a table the contract does not know",
        "api_token.prefix: missing",
        "datasets.concept_doi: a column the contract does not know",
        "hubfiles.name: varchar(255), the contract says varchar(120)",
        "user.email: collation utf8mb4_unicode_ci, the contract says utf8mb4_bin",
        "user.role: NULL, the contract says NOT NULL",
    ]


def test_heads_and_versions_are_held_to_the_contract(contract):
    applied = {name: entry["head"] for name, entry in contract.features.items()}
    assert contract_module.head_differences(contract, applied) == []
    expected = applied["splent_feature_dataset"]
    applied["splent_feature_dataset"] = "dataset9999_something"
    # A feature of a later milestone (dataset_api), which no contract knows yet.
    applied["splent_feature_dataset_api"] = "dataset_api0001"
    assert contract_module.head_differences(contract, applied) == [
        f"splent_feature_dataset at dataset9999_something, the contract expects {expected}",
        "splent_feature_dataset_api migrated, a feature the contract does not know",
    ]
    auth = contract.features["splent_feature_auth"]
    # Against what is installed, so an editable checkout's own differences
    # are left out: only what the test changed may add one.
    already = set(contract_module.version_differences(contract))
    # Another release with the same head is no difference: it changed no
    # migration, so the migrator reads the same schema.
    released = replace(
        contract,
        features=dict(
            contract.features,
            splent_feature_auth={"version": "1.0.0", "head": auth["head"]},
        ),
    )
    assert set(contract_module.version_differences(released)) == already
    # Another head is.
    moved = replace(
        contract,
        features=dict(
            contract.features,
            splent_feature_auth={"version": auth["version"], "head": "x"},
        ),
    )
    installed = contract_module.installed_version("splent_feature_auth")
    head = contract_module.installed_head("splent_feature_auth")
    assert set(contract_module.version_differences(moved)) - already == {
        f"splent_feature_auth {installed} ends its migrations at {head}, "
        "the contract expects x"
    }
