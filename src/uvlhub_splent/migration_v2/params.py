"""What a run is given: the database server, T0 and the decisions (§3.4, E0).

Nothing here reads the app's MARIADB_* variables. The migrator names the
server and the accounts it uses explicitly, so a run can never fall back on
the development database or the shared test one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from uvlhub_splent.migration_v2 import DERIVED, NOT_YET, STAGES


class Refused(Exception):
    """A stage refused to go on. ``reasons`` says why, one line each.

    Not a crash: the pipeline writes the report of what it did up to there,
    and the command exits with a code of its own.
    """

    def __init__(self, stage: str, reasons):
        self.stage = stage
        self.reasons = [reasons] if isinstance(reasons, str) else list(reasons)
        super().__init__(f"{stage} refused: " + "; ".join(self.reasons))


@dataclass(frozen=True)
class Server:
    """The MariaDB server of the cutover and the two accounts on it.

    ``user`` is the migrator account (§3.4), the only one with CREATE and
    DROP on uvlhub3, uvlhub_v2_src and the work schemas. ``root_user``
    restores the dump (sql_log_bin=0 and the DEFINERs need it) and reads
    every connection of the server for E0.

    ``port`` is the server's, for the migrator and for the processes that
    run the features' commands, which take it as MARIADB_PORT.
    """

    host: str
    port: int = 3306
    user: str = "migrator"
    password: str = field(default="", repr=False)
    root_user: str = "root"
    root_password: str = field(default="", repr=False)


@dataclass(frozen=True)
class Params:
    server: Server
    # The moment of the cutover, in UTC. Every date the migrator writes is
    # T0 or comes from the source, never now() (principle 2).
    t0: datetime
    # MIGRATION_EXPECTED_HEAD: the Alembic head of the v2.12 deployed.
    expected_head: str
    # MIGRATION_ADMIN_EMAILS (DM-13): the only accounts loaded as admin.
    admin_emails: tuple[str, ...] = ()
    dump: Path | None = None
    # The hubfile store (HUBFILE_STORAGE_ROOT) and, inside it on the same
    # mount, the mirror of v2.12's uploads/ the operator rsyncs (§6.2).
    store_root: Path | None = None
    report: Path | None = None
    operator: str = ""
    # --force with a B2 taken in the last 15 minutes lets E0 run over a
    # uvlhub3 that may have opened.
    force: bool = False
    b2: Path | None = None
    # Rehearsals (R0, R1) go on past open conflicts and list them; the
    # cutover stops at the first stage that leaves one.
    allow_open_conflicts: bool = False
    # MIGRATION_ID_MARGIN and the rounding of §4.1.
    id_margin: int = 1000
    id_round: int = 10000
    # D12.
    ttl_write_days: int = 90
    ttl_read_days: int = 365
    never_used_grace_days: int = 30
    unused_days: int = 365
    # DM-3: a draft with no file, no DOI and no deposition, older than this.
    ghost_draft_days: int = 30
    source_schema: str = "uvlhub_v2_src"
    # The clean v2.12 that E2 makes to compare the source with (P-00).
    reference_schema: str = "uvlhub_v2_ref"
    target_schema: str = "uvlhub3"
    work_schema: str = "uvlhub_migration"
    inputs_schema: str = "uvlhub_migration_inputs"
    # The features' commands, run in a process of their own (E3, E8, E9).
    upgrade_command: tuple[str, ...] = ("splent", "db:upgrade")
    files_command: tuple[str, ...] = ("splent", "feature:hubfile", "storage-migrate")
    # E9 (DM-6): what it makes again, and the features' commands for it.
    derived: tuple[str, ...] = DERIVED
    factlabel_commands: tuple[tuple[str, ...], ...] = (
        ("splent", "feature:factlabel", "generate"),
        ("splent", "feature:factlabel", "metrics-backfill", "--force"),
    )
    formats_command: tuple[str, ...] = ("splent", "feature:uvl", "generate")
    reindex_command: tuple[str, ...] = ("splent", "feature:explore", "reset")
    stages: tuple[str, ...] = tuple(s for s in STAGES if s not in NOT_YET)

    @property
    def mirror(self) -> Path | None:
        return self.store_root / ".legacy_mirror" if self.store_root else None


def parse_t0(text: str) -> datetime:
    """T0 from ISO 8601, as the naive UTC every DATETIME column holds.

    A time with a zone is converted to UTC; one without is taken as UTC.
    """
    value = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def split_list(value) -> tuple[str, ...]:
    """A comma separated setting (MIGRATION_ADMIN_EMAILS), or a list of them."""
    if not value:
        return ()
    items = value.split(",") if isinstance(value, str) else value
    found = []
    for item in items:
        for part in str(item).split(","):
            if part.strip():
                found.append(part.strip())
    return tuple(found)
