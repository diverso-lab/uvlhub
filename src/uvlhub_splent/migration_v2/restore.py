"""E1, the working source: the dump of v2.12 restored in uvlhub_v2_src (§3.4).

As root, because sql_log_bin=0 and the DEFINERs need it: the keys of
api_keys are in clear in the dump, and they must not reach the binary logs
of 3.0's server (§5.5). event_scheduler goes OFF first, so no event of the
dump ever runs. The dump is B1's logical copy, made without --databases so
it restores into any schema (§9.6).

Then it writes down what the later stages need from the source as it was:
the dump's sha256, the Alembic head (P-19), the AUTO_INCREMENT counter of
every table (§4.1), and the triggers, routines, events and views (P-28).
Those should not exist, since 3306 was exposed (R-26): they are listed in
the run and dropped from uvlhub_v2_src, so none of them acts on the reads
that follow.

B0 (C-29, DM-17), when the run is given one, is the dump of ds_meta_data
that the upgrade notes of the hotfix D1 take before its revision
f7a8b9c0d1e2 cleans the descriptions in place, keeping no copy. E1 restores
it as root in a schema of its own, reads the descriptions E5 quarantines as
the originals, and drops it at once: nothing else of it is needed, and no
copy of it stays on the server of 3.0 (R-08).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile

import sqlalchemy as sa

from uvlhub_splent.migration_v2.db import quote
from uvlhub_splent.migration_v2.params import Refused

# P-28, as the plan writes it.
UNEXPECTED_OBJECTS = """
SELECT 'trigger', trigger_name FROM information_schema.triggers WHERE trigger_schema = :s
UNION ALL SELECT routine_type, routine_name FROM information_schema.routines WHERE routine_schema = :s
UNION ALL SELECT 'event', event_name FROM information_schema.events WHERE event_schema = :s
UNION ALL SELECT 'view', table_name FROM information_schema.views WHERE table_schema = :s
"""

_DROP = {
    "trigger": "DROP TRIGGER IF EXISTS",
    "PROCEDURE": "DROP PROCEDURE IF EXISTS",
    "FUNCTION": "DROP FUNCTION IF EXISTS",
    "event": "DROP EVENT IF EXISTS",
    "view": "DROP VIEW IF EXISTS",
}


def sha256_of(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _client() -> str:
    for name in ("mariadb", "mysql"):
        found = shutil.which(name)
        if found:
            return found
    raise Refused("E1", "no mariadb client on PATH to restore the dump with")


def restore_dump(server, schema: str, dump, what: str = "the dump") -> None:
    """Pipe ``dump`` into ``schema`` with the mariadb client, as root, with
    sql_log_bin off for the session."""
    with tempfile.TemporaryDirectory(prefix="migration-v2-") as folder:
        # The password goes in a file only this process can read, never on
        # the command line, where the processlist of the host shows it.
        defaults = os.path.join(folder, "client.cnf")
        with open(os.open(defaults, os.O_WRONLY | os.O_CREAT, 0o600), "w") as handle:
            handle.write(f"[client]\npassword={server.root_password}\n")
        command = [
            _client(),
            f"--defaults-extra-file={defaults}",
            f"--host={server.host}",
            f"--port={server.port}",
            f"--user={server.root_user}",
            "--default-character-set=utf8mb4",
            "--init-command=SET SESSION sql_log_bin = 0",
            schema,
        ]
        with open(dump, "rb") as source:
            result = subprocess.run(
                command, stdin=source, capture_output=True, check=False
            )
    if result.returncode != 0:
        tail = result.stderr.decode("utf-8", "replace").strip().splitlines()[-5:]
        raise Refused("E1", [f"{what} did not restore"] + tail)


def restore(ctx) -> None:
    params = ctx.params
    if params.dump is None or not params.dump.is_file():
        raise Refused("E1", f"no dump at {params.dump}")
    schema = params.source_schema
    ctx.facts["dump"] = str(params.dump)
    ctx.facts["dump_sha256"] = sha256_of(params.dump)

    with ctx.root.connect() as connection:
        connection.exec_driver_sql("SET GLOBAL event_scheduler = OFF")
        connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {quote(schema)}")
        connection.exec_driver_sql(f"CREATE DATABASE {quote(schema)}")
        connection.commit()

    restore_dump(params.server, schema, params.dump)

    with ctx.root.connect() as connection:
        objects = connection.execute(sa.text(UNEXPECTED_OBJECTS), {"s": schema}).all()
        for kind, name in objects:
            connection.exec_driver_sql(f"{_DROP[kind]} {quote(schema)}.{quote(name)}")
        connection.commit()
        ctx.facts["p28_objects"] = [f"{kind} {name}" for kind, name in objects]

        heads = connection.execute(
            sa.text(f"SELECT version_num FROM {quote(schema)}.alembic_version")
        ).scalars()
        heads = sorted(heads)
        ctx.facts["source_head"] = ", ".join(heads)
        if heads != [params.expected_head]:
            raise Refused(
                "E1",
                f"the dump is at {', '.join(heads) or 'no head'}, "
                f"MIGRATION_EXPECTED_HEAD is {params.expected_head} (P-19)",
            )

        counters = connection.execute(
            sa.text(
                "SELECT table_name, auto_increment FROM information_schema.tables "
                "WHERE table_schema = :s AND table_type = 'BASE TABLE'"
            ),
            {"s": schema},
        ).all()
        ctx.source_counters = {table: counter for table, counter in counters}
        ctx.facts["source_counters"] = ctx.source_counters

    restore_b0(ctx)


def restore_b0(ctx) -> None:
    """C-29: the descriptions of B0 by metadata id in ctx.b0, None without
    a B0. The schema it is restored in goes as soon as they are read."""
    params = ctx.params
    ctx.b0 = None
    ctx.facts["b0"] = None
    if params.b0 is None:
        return
    if not params.b0.is_file():
        raise Refused("E1", f"no B0 at {params.b0}")
    schema = quote(params.b0_schema)
    with ctx.root.connect() as connection:
        connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {schema}")
        connection.exec_driver_sql(f"CREATE DATABASE {schema}")
        connection.commit()
    try:
        restore_dump(params.server, params.b0_schema, params.b0, what="B0")
        with ctx.root.connect() as connection:
            found = connection.execute(
                sa.text(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = :s AND table_name = 'ds_meta_data'"
                ),
                {"s": params.b0_schema},
            ).scalar()
            if not found:
                raise Refused("E1", f"B0 ({params.b0}) holds no ds_meta_data")
            rows = connection.execute(
                sa.text(f"SELECT id, description FROM {schema}.ds_meta_data")
            ).all()
            connection.rollback()
    finally:
        with ctx.root.connect() as connection:
            connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {schema}")
            connection.commit()
    ctx.b0 = {row.id: row.description or "" for row in rows}
    ctx.facts["b0"] = {
        "path": str(params.b0),
        "sha256": sha256_of(params.b0),
        "rows": len(ctx.b0),
    }
