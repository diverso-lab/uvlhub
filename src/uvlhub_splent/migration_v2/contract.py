"""The data contract (MIG-03): contract.toml, and how a schema is held to it.

E3 compares uvlhub3 with it once the features' migrations have run, and
stops on any difference; tests/migration_v2/test_contract.py does the same
on the schema the pinned features create, so a pin that changes a table the
migration fills fails there first.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import cache
from importlib import metadata
from pathlib import Path

import sqlalchemy as sa

CONTRACT_FILE = Path(__file__).with_name("contract.toml")

LOAD, READ, EMPTY = "load", "read", "empty"

# Tables a schema at head has that no feature's model declares: Alembic's
# own, one per feature.
ALEMBIC_PREFIX = "alembic_"


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    nullable: bool
    collation: str | None = None
    dm15: str | None = None
    source: str | None = None
    rule: str | None = None
    on_null: str | None = None


@dataclass(frozen=True)
class Table:
    name: str
    owner: str
    role: str
    columns: dict[str, Column]


@dataclass(frozen=True)
class Contract:
    version: int
    charset: str
    collation: str
    features: dict[str, dict]
    source_heads: tuple[str, ...]
    scopes: dict[str, str]
    dm15_missing: tuple[str, ...]
    tables: dict[str, Table]

    def by_role(self, role: str) -> list[Table]:
        return [table for table in self.tables.values() if table.role == role]

    def collations(self) -> list[tuple[str, str, str]]:
        """(table, column, collation) of every text column the contract
        names, what contract_collation holds for V-14."""
        return [
            (table.name, column.name, column.collation)
            for table in self.tables.values()
            for column in table.columns.values()
            if column.collation
        ]

    def dm15_pending(self) -> list[str]:
        """What DM-15 asks for and the pinned features do not give yet."""
        pending = [
            f"{table.name}.{column.name}: {column.collation}, DM-15 asks {column.dm15}"
            for table in self.tables.values()
            for column in table.columns.values()
            if column.dm15 and column.dm15 != column.collation
        ]
        return pending + [f"{name}: no such column yet" for name in self.dm15_missing]


def parse(text: str) -> Contract:
    data = tomllib.loads(text)
    tables = {}
    for name, entry in data["tables"].items():
        columns = {
            column: Column(
                name=column,
                type=spec["type"],
                nullable=spec["nullable"],
                collation=spec.get("collation"),
                dm15=spec.get("dm15"),
                source=spec.get("source"),
                rule=spec.get("rule"),
                on_null=spec.get("on_null"),
            )
            for column, spec in (entry.get("columns") or {}).items()
        }
        tables[name] = Table(name, entry["owner"], entry["role"], columns)
    return Contract(
        version=data["contract"]["version"],
        charset=data["database"]["charset"],
        collation=data["database"]["collation"],
        features=data["features"],
        source_heads=tuple(data["source"]["heads"]),
        scopes=data["scopes"],
        dm15_missing=tuple(data.get("dm15", {}).get("missing", ())),
        tables=tables,
    )


@cache
def load() -> Contract:
    return parse(CONTRACT_FILE.read_text(encoding="utf-8"))


# ── Holding a schema to it ───────────────────────────────────────────────


def schema_columns(connection, schema: str) -> dict[str, dict[str, dict]]:
    """Every column of ``schema`` as information_schema has it, by table."""
    rows = connection.execute(
        sa.text(
            "SELECT table_name, column_name, column_type, is_nullable, collation_name "
            "FROM information_schema.columns WHERE table_schema = :s "
            "ORDER BY table_name, ordinal_position"
        ),
        {"s": schema},
    ).all()
    found: dict[str, dict[str, dict]] = {}
    for table, column, column_type, nullable, collation in rows:
        found.setdefault(table, {})[column] = {
            "type": column_type,
            "nullable": nullable == "YES",
            "collation": collation,
        }
    return found


def differences(contract: Contract, columns: dict[str, dict[str, dict]]) -> list[str]:
    """Where a schema (schema_columns) is not what the contract says, one
    line each. [] when it is.

    Every table must be known (zero unknowns): a feature that adds one
    makes this fail until the contract says whether the migration fills it.
    A load table has exactly the contract's columns; a read table at least
    the ones it lists.
    """
    found = []
    known = set(contract.tables)
    for table in sorted(columns):
        if table not in known and not table.startswith(ALEMBIC_PREFIX):
            found.append(f"{table}: a table the contract does not know")
    for name, table in sorted(contract.tables.items()):
        actual = columns.get(name)
        if actual is None:
            found.append(f"{name}: missing ({table.owner})")
            continue
        if table.role == LOAD:
            for column in sorted(set(actual) - set(table.columns)):
                found.append(f"{name}.{column}: a column the contract does not know")
        for column in table.columns.values():
            have = actual.get(column.name)
            where = f"{name}.{column.name}"
            if have is None:
                found.append(f"{where}: missing")
                continue
            if have["type"] != column.type:
                found.append(
                    f"{where}: {have['type']}, the contract says {column.type}"
                )
            if have["nullable"] != column.nullable:
                found.append(
                    f"{where}: {'NULL' if have['nullable'] else 'NOT NULL'}, "
                    f"the contract says {'NULL' if column.nullable else 'NOT NULL'}"
                )
            if have["collation"] != column.collation:
                found.append(
                    f"{where}: collation {have['collation']}, "
                    f"the contract says {column.collation}"
                )
    return found


def installed_version(feature: str) -> str | None:
    try:
        return metadata.version(feature)
    except metadata.PackageNotFoundError:
        return None


def version_differences(contract: Contract) -> list[str]:
    """The features installed in another version than the contract's (E0)."""
    found = []
    for feature, entry in sorted(contract.features.items()):
        installed = installed_version(feature)
        if installed != entry["version"]:
            found.append(
                f"{feature} is {installed or 'not installed'}, the contract was "
                f"written for {entry['version']}"
            )
    return found


def head_differences(contract: Contract, applied: dict[str, str | None]) -> list[str]:
    """Where splent_migrations (``applied``) is not the contract's heads (V-12)."""
    found = []
    for feature, entry in sorted(contract.features.items()):
        head = applied.get(feature)
        if head != entry["head"]:
            found.append(f"{feature} at {head}, the contract expects {entry['head']}")
    for feature in sorted(set(applied) - set(contract.features)):
        found.append(f"{feature} migrated, a feature the contract does not know")
    return found
