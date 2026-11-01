"""The migrator's connections: SQLAlchemy Core, on engines of its own.

Never the ORM, never ``db.session``, never the app's engine. The listeners
that matter are the features' (dataset's after_insert that makes DSMetrics,
hubfile's Session.after_commit that dispatches tasks): a Core insert on a
connection of its own fires none of them.

Every connection is set up the same way when it opens: UTC, so a
TIMESTAMP or a NOW() reads as the DATETIME columns are written (the
monolith stored naive UTC, and so does 3.0), and a strict sql_mode, so a
value that does not fit is an error and never a silent truncation.
"""

from __future__ import annotations

from contextlib import contextmanager
from itertools import islice

import sqlalchemy as sa
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool

STRICT_SQL_MODE = (
    "STRICT_ALL_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,"
    "ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION"
)

# One transaction per batch, in id order (§3.4).
BATCH_SIZE = 1000


def make_engine(host: str, port: int, user: str, password: str) -> sa.Engine:
    """An engine on the server, with no default database: every name the
    migrator writes is qualified with its schema."""
    url = URL.create(
        "mysql+pymysql",
        username=user,
        password=password,
        host=host,
        port=port,
        query={"charset": "utf8mb4"},
    )
    # No pool: a connection the migrator leaves is closed, and the
    # processlist E0 reads shows only what is in use.
    engine = sa.create_engine(url, poolclass=NullPool)

    @sa.event.listens_for(engine, "connect")
    def _session_settings(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET time_zone = '+00:00'")
        cursor.execute(f"SET SESSION sql_mode = '{STRICT_SQL_MODE}'")
        cursor.close()

    return engine


def quote(name: str) -> str:
    """A schema, table or column name, quoted for MariaDB."""
    return "`" + name.replace("`", "``") + "`"


def qualified(schema: str, table: str) -> str:
    return f"{quote(schema)}.{quote(table)}"


def reflect(connection, schema: str, only=None) -> dict[str, sa.Table]:
    """The tables of ``schema`` as Core tables, by their bare names.

    Reflected, never imported from a feature's models: the migrator depends
    on the tables the contract names, not on module paths that move.
    """
    metadata = sa.MetaData()
    metadata.reflect(bind=connection, schema=schema, only=only)
    return {table.name: table for table in metadata.tables.values()}


def all_rows(connection, table: sa.Table, order: str = "id") -> list[dict]:
    """Every row of ``table`` as a dict, in ``order``: a stable order, so a
    run gives the same database every time (principle 2)."""
    statement = sa.select(table).order_by(table.c[order])
    return [dict(row) for row in connection.execute(statement).mappings()]


def batched(rows, size: int = BATCH_SIZE):
    iterator = iter(rows)
    while chunk := list(islice(iterator, size)):
        yield chunk


@contextmanager
def foreign_keys_off(connection):
    """Foreign key checks off on ``connection`` while the block loads.

    MariaDB does not check the rows again when they come back on, so
    whoever loads with them off checks every foreign key afterwards
    (verify.foreign_key_orphans, V-04).
    """
    connection.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0")
    connection.commit()
    try:
        yield connection
    finally:
        connection.rollback()
        connection.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1")
        connection.commit()


def insert_batches(connection, table: sa.Table, rows, key: str = "id") -> int:
    """Insert ``rows`` (dicts) into ``table`` in batches by ``key``, one
    transaction each. Answers how many went in.

    Whatever the connection was reading ends first: a batch is a
    transaction of its own."""
    if connection.in_transaction():
        connection.commit()
    ordered = sorted(rows, key=lambda row: row[key])
    count = 0
    for chunk in batched(ordered):
        with connection.begin():
            connection.execute(table.insert(), chunk)
        count += len(chunk)
    return count


def scalar(connection, sql: str, **params):
    return connection.execute(sa.text(sql), params).scalar()


def schema_exists(connection, schema: str) -> bool:
    return bool(
        scalar(
            connection,
            "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = :s",
            s=schema,
        )
    )


def table_exists(connection, schema: str, table: str) -> bool:
    return bool(
        scalar(
            connection,
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = :s AND table_name = :t",
            s=schema,
            t=table,
        )
    )
