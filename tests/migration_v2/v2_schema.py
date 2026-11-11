"""The schema of uvlhub.io 2.12, from the monolith's own migrations.

R0 starts from "a v2.12 database created with the monolith's migrations up
to the head deployed" (§9.1), and E2 compares the dump with the same
schema (P-00). The monolith is not part of this repository, so its DDL is
kept in the migrator's package (uvlhub.migration_v2.v2_12_schema),
made by running its Alembic chain here; test_v2_schema.py runs the chain
again when the monolith is in the workspace (_reference/uvlhub_monolith)
and fails when the two differ. After R1, the production DDL (mariadb-dump
--no-data) is what the tests start from.

The chain runs without the monolith's env.py, which needs its app: every
revision up to the head is imported from its file, in order, and its
upgrade() run on a connection through Alembic's operations. The monolith's
folder is only read: nothing is compiled into it.

    python tests/migration_v2/v2_schema.py <host> <root password>

writes the DDL it makes into v2_12_schema.py, in the place of the one
there.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import sqlalchemy as sa

from uvlhub.migration_v2 import v2_12_schema

WORKSPACE = Path(__file__).resolve().parents[3]
MONOLITH_VERSIONS = (
    WORKSPACE / "_reference" / "uvlhub_monolith" / "migrations" / "versions"
)
VENDORED = Path(v2_12_schema.__file__)
# The release; the hotfix's f7a8b9c0d1e2 only rewrites descriptions, and
# imports bleach, which the product does not have.
HEAD = v2_12_schema.HEAD

_REVISION = re.compile(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", re.M)
_DOWN = re.compile(r"^down_revision\s*=\s*(.+)$", re.M)
_ID = re.compile(r"['\"]([^'\"]+)['\"]")


def revisions(
    folder: Path = MONOLITH_VERSIONS,
) -> dict[str, tuple[Path, tuple[str, ...]]]:
    """revision -> (script, parents), read from the scripts' headers."""
    found = {}
    for script in sorted(folder.glob("*.py")):
        text = script.read_text(encoding="utf-8")
        revision = _REVISION.search(text)
        down = _DOWN.search(text)
        if revision and down:
            found[revision.group(1)] = (script, tuple(_ID.findall(down.group(1))))
    return found


def chain(head: str = HEAD, folder: Path = MONOLITH_VERSIONS) -> list[Path]:
    """The scripts from the first revision to ``head``, parents first."""
    known = revisions(folder)
    needed, pending = set(), [head]
    while pending:
        revision = pending.pop()
        if revision not in needed:
            needed.add(revision)
            pending.extend(known[revision][1])
    ordered, done = [], set()
    while len(ordered) < len(needed):
        ready = sorted(r for r in needed - done if all(p in done for p in known[r][1]))
        ordered.append(known[ready[0]][0])
        done.add(ready[0])
    return ordered


def _load(script: Path):
    spec = importlib.util.spec_from_file_location(f"v2_12_{script.stem}", script)
    module = importlib.util.module_from_spec(spec)
    writes = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = writes
    return module


def apply_chain(connection, head: str = HEAD) -> None:
    """Create v2.12's tables on ``connection`` (its default database) as the
    chain up to ``head`` does, and stamp it."""
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext

    context = MigrationContext.configure(connection)
    with Operations.context(context):
        for script in chain(head):
            _load(script).upgrade()
    connection.exec_driver_sql(
        "CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL, "
        "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
    )
    connection.exec_driver_sql(f"INSERT INTO alembic_version VALUES ('{head}')")
    connection.commit()


def ddl(connection) -> str:
    """Every CREATE TABLE of the connection's database, in name order,
    without the counters, as one script."""
    tables = connection.exec_driver_sql(
        "SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'"
    ).all()
    statements = []
    for table, _kind in sorted(tables):
        create = connection.exec_driver_sql(f"SHOW CREATE TABLE `{table}`").one()[1]
        statements.append(re.sub(r" AUTO_INCREMENT=\d+", "", create) + ";")
    return (
        "SET FOREIGN_KEY_CHECKS = 0;\n\n"
        + "\n\n".join(statements)
        + "\n\nSET FOREIGN_KEY_CHECKS = 1;\n"
    )


def write_module(text: str, module: Path = VENDORED) -> None:
    """Put ``text`` in the place of the DDL v2_12_schema.py holds."""
    source = module.read_text(encoding="utf-8")
    start = source.index('DDL = """\\\n') + len('DDL = """\\\n')
    end = source.index('"""', start)
    module.write_text(source[:start] + text + source[end:], encoding="utf-8")


def build_ddl(
    host: str, root_password: str, port: int = 3306, schema: str = "uvlhub_v2_ref"
) -> str:
    """The DDL of the chain, made in a scratch schema that is dropped after."""
    url = sa.engine.URL.create(
        "mysql+pymysql",
        username="root",
        password=root_password,
        host=host,
        port=port,
        query={"charset": "utf8mb4"},
    )
    engine = sa.create_engine(url, poolclass=sa.pool.NullPool)
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql(f"DROP DATABASE IF EXISTS `{schema}`")
            connection.exec_driver_sql(f"CREATE DATABASE `{schema}`")
            connection.exec_driver_sql(f"USE `{schema}`")
            apply_chain(connection)
            text = ddl(connection)
            connection.exec_driver_sql(f"DROP DATABASE `{schema}`")
            connection.commit()
    finally:
        engine.dispose()
    return text


if __name__ == "__main__":
    write_module(build_ddl(sys.argv[1], sys.argv[2]))
