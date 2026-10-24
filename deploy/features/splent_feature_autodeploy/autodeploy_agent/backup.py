"""Database backups taken before every deploy, and the restore a rollback runs.

The dump runs inside the product's MariaDB container as root, with the
credentials that container already holds in its own environment
(``MARIADB_ROOT_PASSWORD`` and ``MARIADB_DATABASE``). They are read by the
shell inside that container and handed to the client through ``MYSQL_PWD``,
so they never travel through the agent, never appear in a process list and
are never printed.

A backup is ``<UTC timestamp>-<short id of the image being replaced>.sql.gz``
under ``/data/backups``. It is written under a temporary name and only takes
its real one once ``mariadb-dump`` has exited cleanly and the dump ends with
its ``Dump completed`` trailer, so a file with a real name is a complete
dump. The newest ``AUTODEPLOY_KEEP_BACKUPS`` are kept.

That dump is the rollback's: on the same host, unencrypted (0600, in the
agent's volume), restored in seconds. The copy that survives the host is
the backup feature's (splent_feature_backup), which :func:`run_in_container`
takes in the web container first when the product has it: encrypted to
keys the server does not hold, so the agent could not restore it anyway.

:meth:`BackupManager.schema` is what tells a rollback whether the database
has to go back at all: a fingerprint of every table's columns and every
migration revision, taken before the deploy and again when it fails.
"""

from __future__ import annotations

import gzip
import hashlib
import logging
import os
import tarfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from autodeploy_agent.dockerops import exec_output, exec_stream

logger = logging.getLogger("autodeploy.backup")

BACKUP_SUFFIX = ".sql.gz"
PARTIAL_SUFFIX = ".partial"
DUMP_TRAILER = b"Dump completed"

#: Where the restore copies the dump inside the database container.
RESTORE_FILE = "splent-autodeploy-restore.sql.gz"
RESTORE_DIR = "/tmp"

# Both scripts run under bash inside the MariaDB image (Ubuntu based, so bash
# and gzip are there). Older images name the variables MYSQL_*, so those are
# the fallback.
_CREDENTIALS = r"""
set -euo pipefail
pw="${MARIADB_ROOT_PASSWORD:-${MYSQL_ROOT_PASSWORD:-}}"
db="${MARIADB_DATABASE:-${MYSQL_DATABASE:-}}"
if [ -z "$pw" ]; then echo "MARIADB_ROOT_PASSWORD is not set in the database container" >&2; exit 3; fi
if [ -z "$db" ]; then echo "MARIADB_DATABASE is not set in the database container" >&2; exit 3; fi
export MYSQL_PWD="$pw"
"""

DUMP_SCRIPT = (
    _CREDENTIALS
    + r"""
exec mariadb-dump -uroot --single-transaction --routines --triggers "$db"
"""
)

# Dropping the database first matters: tables the new image's migrations
# created would otherwise survive the import, and the old code would find a
# schema it never knew.
RESTORE_SCRIPT = (
    _CREDENTIALS
    + rf"""
f="{RESTORE_DIR}/{RESTORE_FILE}"
trap 'rm -f "$f"' EXIT
mariadb -uroot -e "DROP DATABASE IF EXISTS \`$db\`; CREATE DATABASE \`$db\`;"
gunzip -c "$f" | mariadb -uroot "$db"
"""
)


# The columns of every table, and the content of the tables that record the
# migrations (alembic_version, each feature's alembic_<feature>, and
# splent_migrations). Any migration changes one or the other, a failed one
# that left half of its DDL behind included.
SCHEMA_SCRIPT = (
    _CREDENTIALS
    + r"""
q() { mariadb -uroot -N -B "$db" -e "$1"; }
q "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COALESCE(COLUMN_DEFAULT, '') FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME, ORDINAL_POSITION"
for t in $(q "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND (TABLE_NAME LIKE 'alembic%' OR TABLE_NAME = 'splent_migrations') ORDER BY TABLE_NAME"); do
  echo "== $t"
  q "SELECT * FROM \`$t\` ORDER BY 1"
done
"""
)


class BackupError(RuntimeError):
    """The dump did not complete, so there is no backup to roll back to."""


class RestoreError(RuntimeError):
    """The database could not be put back from the backup."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _tail(data: bytes, size: int = 600) -> str:
    return data[-size:].decode("utf-8", errors="replace").strip()


class BackupManager:
    def __init__(
        self,
        api,
        db_container: str,
        backups_dir: str | os.PathLike,
        keep: int,
        clock: Callable[[], datetime] = _utcnow,
    ):
        self.api = api
        self.db_container = db_container
        self.dir = Path(backups_dir)
        self.keep = max(1, int(keep))
        self.clock = clock

    def list(self) -> list[Path]:
        """Complete backups, newest first."""
        if not self.dir.is_dir():
            return []
        return sorted(
            (p for p in self.dir.iterdir() if p.name.endswith(BACKUP_SUFFIX)),
            key=lambda p: p.name,
            reverse=True,
        )

    def create(self, label: str) -> Path:
        """Dump the product database to a new backup and return its path."""
        self.dir.mkdir(parents=True, exist_ok=True)
        stamp = self.clock().strftime("%Y%m%dT%H%M%SZ")
        final = self.dir / f"{stamp}-{label or 'unknown'}{BACKUP_SUFFIX}"
        partial = final.with_name(final.name + PARTIAL_SUFFIX)

        tail = b""
        errors = b""
        try:
            exec_id, chunks = exec_stream(
                self.api, self.db_container, ["bash", "-c", DUMP_SCRIPT]
            )
            # The dump holds password hashes and API token hashes: readable by
            # the agent alone from the moment it exists.
            fd = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with (
                os.fdopen(fd, "wb") as raw,
                gzip.GzipFile(fileobj=raw, mode="wb") as out,
            ):
                for stdout, stderr in chunks:
                    if stdout:
                        out.write(stdout)
                        tail = (tail + stdout)[-512:]
                    if stderr:
                        errors = (errors + stderr)[-2000:]
            code = self.api.exec_inspect(exec_id).get("ExitCode")
        except Exception as exc:
            partial.unlink(missing_ok=True)
            raise BackupError(f"the dump could not run: {exc}") from exc

        if code != 0:
            partial.unlink(missing_ok=True)
            raise BackupError(
                f"mariadb-dump exited with code {code}: {_tail(errors) or 'no message'}"
            )
        if DUMP_TRAILER not in tail:
            partial.unlink(missing_ok=True)
            raise BackupError(
                "the dump does not end with 'Dump completed', so it is incomplete"
            )
        os.replace(partial, final)
        logger.info("Backed up the database to %s", final.name)
        self.prune(protect=final)
        return final

    def prune(self, protect: Path | None = None) -> list[str]:
        """Delete all but the newest ``keep`` backups. Returns what went."""
        removed = []
        for path in self.list()[self.keep :]:
            if protect is not None and path == protect:
                continue
            try:
                path.unlink()
                removed.append(path.name)
            except OSError as exc:
                logger.warning("Could not delete old backup %s: %s", path.name, exc)
        # A partial file is a dump that died with the agent.
        for path in self.dir.glob(f"*{PARTIAL_SUFFIX}"):
            path.unlink(missing_ok=True)
        return removed

    def schema(self) -> str | None:
        """A fingerprint of the database's schema and migration revisions,
        or None when it cannot be read (the database is down, or empty)."""
        try:
            code, out, _err = exec_output(
                self.api, self.db_container, ["bash", "-c", SCHEMA_SCRIPT]
            )
        except Exception:  # noqa: BLE001 - unknown, which a rollback treats as changed
            return None
        if code != 0 or not out:
            return None
        return hashlib.sha256(out).hexdigest()

    def restore(self, backup: str | os.PathLike) -> None:
        """Drop the product database, recreate it and import ``backup``."""
        backup = Path(backup)
        if not backup.is_file():
            raise RestoreError(f"the backup {backup.name} is missing")

        archive = self.dir / ".restore.tar"
        try:
            with tarfile.open(archive, "w") as tar:
                tar.add(backup, arcname=RESTORE_FILE)
            with open(archive, "rb") as handle:
                self.api.put_archive(self.db_container, RESTORE_DIR, handle)
        except Exception as exc:
            raise RestoreError(
                f"the backup could not be copied into the database container: {exc}"
            ) from exc
        finally:
            archive.unlink(missing_ok=True)

        try:
            code, _out, err = exec_output(
                self.api, self.db_container, ["bash", "-c", RESTORE_SCRIPT]
            )
        except Exception as exc:
            raise RestoreError(f"the import could not run: {exc}") from exc
        if code != 0:
            raise RestoreError(
                f"the import exited with code {code}: {_tail(err) or 'no message'}"
            )
        logger.info("Restored the database from %s", backup.name)


def run_in_container(
    api, container: str, command: list[str], user: str
) -> tuple[int | None, str]:
    """Run ``command`` in ``container`` as ``user``, reading its output as it
    comes (a backup prints a line every half minute, so a long one never
    looks dead). Returns the exit code and the last lines it printed."""
    exec_id, chunks = exec_stream(api, container, command, user=user)
    tail = b""
    for stdout, stderr in chunks:
        for data in (stdout, stderr):
            if data:
                tail = (tail + data)[-2000:]
    code = api.exec_inspect(exec_id).get("ExitCode")
    return code, _tail(tail, 1200)
