"""E0, preflight: the safeguards that keep the migrator off real work (§3.4).

The migrator drops and creates uvlhub3 on every run, so the worst it can do
is run once 3.0 has opened. It refuses:

- when uvlhub3 shows signs of use: a run that completed (the event
  migration.completed of the plan; 3.0 has no audit table for it yet, so
  the previous run's row in uvlhub_migration.run stands for it), a row
  created after T0, a mail the outbox sent, an account that signed in, or
  a row in a table the migration leaves empty. --force lets it go on, but
  only with a B2 taken in the last 15 minutes;
- when the server has connections from anyone but the migrator and root
  (SHOW PROCESSLIST): the web and the worker of 3.0 are not created until
  E10 is done;
- when RUN_DB_SEED is not false: the processes it starts must never seed;
- when it cannot take GET_LOCK('uvlhub_migration', 0): another run is on.

It also refuses parameters it cannot keep its word with: an unknown head,
a token life apikeys does not give, features of other versions than the
contract was written for.
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

import sqlalchemy as sa
from splent_io.splent_feature_apikeys.services import MAX_TTL_DAYS

from uvlhub_splent.migration_v2 import contract as contract_module
from uvlhub_splent.migration_v2.db import qualified, schema_exists, table_exists
from uvlhub_splent.migration_v2.params import Refused

LOCK_NAME = "uvlhub_migration"
# A B2 older than this does not let --force through (§3.4).
B2_MAX_AGE_SECONDS = 15 * 60
# Server threads that are no client: they hold no session of their own.
_INTERNAL_COMMANDS = ("Daemon", "Slave_IO", "Slave_SQL", "Binlog Dump")


def acquire_lock(engine):
    """A connection holding GET_LOCK('uvlhub_migration', 0), which the run
    keeps open to the end; None when another run holds it."""
    connection = engine.connect()
    got = connection.execute(
        sa.text("SELECT GET_LOCK(:name, 0)"), {"name": LOCK_NAME}
    ).scalar()
    connection.commit()
    if got != 1:
        connection.close()
        return None
    return connection


def release_lock(connection) -> None:
    if connection is None:
        return
    try:
        connection.execute(sa.text("SELECT RELEASE_LOCK(:name)"), {"name": LOCK_NAME})
        connection.commit()
    finally:
        connection.close()


def foreign_connections(root, allowed_users) -> list[str]:
    """The server's connections that are not the migrator's or root's, as
    'user@host (db)' lines."""
    with root.connect() as connection:
        rows = connection.execute(
            sa.text(
                "SELECT id, user, host, db, command FROM information_schema.processlist "
                "WHERE id <> CONNECTION_ID()"
            )
        ).all()
    return [
        f"{user}@{(host or '').split(':')[0]} ({db or 'no database'})"
        for _id, user, host, db, command in rows
        if user not in allowed_users and command not in _INTERNAL_COMMANDS
    ]


def signs_of_use(engine, params, contract) -> list[str]:
    """What says uvlhub3 has been used since the last run filled it."""
    found = []
    with engine.connect() as connection:
        if table_exists(connection, params.work_schema, "run"):
            done = connection.execute(
                sa.text(
                    f"SELECT id, completed_at FROM {qualified(params.work_schema, 'run')} "
                    "WHERE completed_at IS NOT NULL ORDER BY id DESC LIMIT 1"
                )
            ).first()
            if done is not None:
                found.append(
                    f"a run completed at {done.completed_at:%Y-%m-%d %H:%M:%S} "
                    "(migration.completed): 3.0 may have opened since"
                )
        target = params.target_schema
        if not schema_exists(connection, target):
            return found
        dated = connection.execute(
            sa.text(
                "SELECT table_name FROM information_schema.columns "
                "WHERE table_schema = :s AND column_name = 'created_at' "
                "AND data_type IN ('datetime', 'timestamp') ORDER BY table_name"
            ),
            {"s": target},
        ).scalars()
        for table in list(dated):
            newer = connection.execute(
                sa.text(
                    f"SELECT COUNT(*) FROM {qualified(target, table)} WHERE created_at > :t0"
                ),
                {"t0": params.t0},
            ).scalar()
            if newer:
                found.append(f"{newer} row(s) of {table} created after T0")
        if table_exists(connection, target, "mail_outbox"):
            sent = connection.execute(
                sa.text(
                    f"SELECT COUNT(*) FROM {qualified(target, 'mail_outbox')} "
                    "WHERE sent_at IS NOT NULL OR state = 'sent'"
                )
            ).scalar()
            if sent:
                found.append(f"{sent} mail(s) sent from the outbox")
        if table_exists(connection, target, "user"):
            signed_in = connection.execute(
                sa.text(
                    f"SELECT COUNT(*) FROM {qualified(target, 'user')} "
                    "WHERE last_login_at IS NOT NULL"
                )
            ).scalar()
            if signed_in:
                found.append(f"{signed_in} account(s) signed in")
        for table in contract.by_role(contract_module.EMPTY):
            if not table_exists(connection, target, table.name):
                continue
            rows = connection.execute(
                sa.text(f"SELECT COUNT(*) FROM {qualified(target, table.name)}")
            ).scalar()
            if rows:
                found.append(
                    f"{rows} row(s) in {table.name}, which the migration leaves empty"
                )
    return found


def fresh_b2(path: Path | None) -> tuple[bool, str]:
    """Whether ``path`` is a B2 taken in the last 15 minutes, and its sha256."""
    if path is None or not path.is_file() or path.stat().st_size == 0:
        return False, ""
    if time.time() - path.stat().st_mtime > B2_MAX_AGE_SECONDS:
        return False, ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return True, digest.hexdigest()


def preflight(ctx) -> None:
    """Run E0. Takes the lock, which ctx keeps, and raises Refused with
    every reason found."""
    params, contract = ctx.params, ctx.contract
    reasons = []

    if params.expected_head not in contract.source_heads:
        reasons.append(
            f"MIGRATION_EXPECTED_HEAD {params.expected_head!r} is not a head of "
            f"v2.12 ({', '.join(contract.source_heads)})"
        )
    if (os.environ.get("RUN_DB_SEED") or "").strip().lower() != "false":
        reasons.append(
            "RUN_DB_SEED is not false: nothing the migrator starts may seed uvlhub3"
        )
    for days in (params.ttl_write_days, params.ttl_read_days):
        if not 1 <= days <= MAX_TTL_DAYS:
            reasons.append(
                f"a token life of {days} days: apikeys gives 1 to {MAX_TTL_DAYS}"
            )
    reasons += contract_module.version_differences(contract)
    # What the parameters say is settled before the server is asked anything.
    if reasons:
        raise Refused("E0", reasons)

    ctx.lock = acquire_lock(ctx.engine)
    if ctx.lock is None:
        raise Refused("E0", f"GET_LOCK('{LOCK_NAME}', 0) is held: another run is on")

    allowed = {params.server.user, params.server.root_user}
    for line in foreign_connections(ctx.root, allowed):
        reasons.append(f"a connection that is not the migrator's: {line}")

    used = signs_of_use(ctx.engine, params, contract)
    if used:
        if not params.force:
            reasons += used
        else:
            fresh, digest = fresh_b2(params.b2)
            if not fresh:
                reasons += used
                reasons.append(
                    "--force needs --b2 with a B2 taken in the last 15 minutes"
                )
            else:
                ctx.facts["forced"] = {
                    "signs_of_use": used,
                    "b2": str(params.b2),
                    "b2_sha256": digest,
                }

    if reasons:
        raise Refused("E0", reasons)
