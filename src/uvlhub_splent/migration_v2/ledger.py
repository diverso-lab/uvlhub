"""The work schemas (§3.5): what a run writes down, and what it is given.

``uvlhub_migration`` holds the outputs and is made again by every run:
nothing is lost in silence (principle 6), so whatever is dropped,
transformed or in conflict is written there with its reason.
``uvlhub_migration_inputs`` holds what people decided and what was fetched
from Zenodo; a run creates its tables when they are missing and never drops
them.

A conflict names the source rows it is about (``source_rows``, table:id)
and their fingerprint. Whoever decides it copies both into a decision: E2
reads those rows again and stops the run when they changed, and a decision
that holds closes its conflict when the stage that finds it raises it (§3.5).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date, datetime

import sqlalchemy as sa

from uvlhub_splent.migration_v2.db import insert_batches, quote
from uvlhub_splent.migration_v2.params import Refused

OPEN, DECIDED = "open", "decided"
# Why a row is not loaded, where many tables share the reason.
SEED, HELD, OWNER_GONE, ORPHAN = (
    "seed",
    "held_by_conflict",
    "owner_not_loaded",
    "orphan",
)


# Every kind of conflict a stage raises, with what the migrator does with
# its rows while it is open (a rehearsal goes on that way): what a decision
# that accepts it keeps. A stage that raises a kind not named here is a bug.
CONFLICTS = {
    # E2
    "schema_drift": "C-26 (P-00): the source differs from the clean v2.12 "
    "there; no rule of the migrator reads the difference",
    # E4
    "email_clash_canonical": "C-13: the accounts are held, with what is theirs",
    "email_clash_collation": "C-13: the accounts are held, with what is theirs",
    "identity_unknown_provider": "C-14: the identity is held",
    "identity_invalid_id": "C-14: the identity is held",
    "identity_second_link": "C-14 (P-11): every identity of the pair is held",
    "identity_other_account": "C-14: the row of orcid or github is held",
    "identity_second_identity": "C-14: the row of orcid or github is held",
    # E5
    "lineage_origin_not_loaded": "C-05: it loads as an original",
    "lineage_no_origin": "C-05: it loads as it is",
    "lineage_branch": "C-05: the branches load as they are",
    "lineage_gap": "C-05: it loads as it is",
    "metadata_shared": "P-03: the datasets load, sharing it",
    "doi_not_zenodo": "C-30: it loads with its DOI",
    "doi_not_its_deposition": "C-30: it loads with its DOI",
    "doi_repeated": "C-10: the datasets load, each with it",
    "file_two_datasets": "C-07: the feature model follows its file's dataset",
    "duplicate_path": "C-11: the name with ~<id> DM-10 gives is another "
    "file's, so the rows keep one path",
    "checksum_unknown": "C-25: the file loads, unverified",
    "tombstone_undated": "C-03 (DM-4): the tombstone is dated T0",
    "tombstone_without_owner": "C-03 (DM-4): no tombstone is made; the DOI "
    "is in uvlhub_migration.tombstone only, and answers 404",
    # E6
    "doi_mapping_cycle": "C-20: the mappings of the cycle load nowhere",
    "doi_mapping_dangling": "C-20: the mapping loads nowhere, so its old DOI "
    "answers 404",
    # E8
    "file_mismatch": "§6.2: a file of a published dataset loads in mismatch",
    "file_missing": "§6.2: a published dataset loads without its file",
    "file_unverified": "§6.2: a file of a published dataset loads unverified",
    "file_conflict": "§6.2: a published dataset's file stays without a key",
}
# What a decision may say. accept: the migrator's own handling of the
# conflict (CONFLICTS) stands, and the conflict is closed.
RESOLUTIONS = ("accept",)
# The table of the sources a conflict of E2 is about, which are no rows of
# the source: E2 raises those again on every run, and a decision on one is
# held to what it finds then.
SCHEMA = "information_schema"


def _outputs(schema: str) -> sa.MetaData:
    metadata = sa.MetaData(schema=schema)
    sa.Table(
        "run",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("migrator_version", sa.String(32), nullable=False),
        sa.Column("contract_version", sa.Integer, nullable=False),
        sa.Column("t0", sa.DateTime, nullable=False),
        sa.Column("operator", sa.String(255)),
        sa.Column("dump", sa.String(1024)),
        sa.Column("dump_sha256", sa.String(64)),
        sa.Column("source_head", sa.String(64)),
        # Parameters, feature versions, stage times, the counters of the
        # source and the ones given to 3.0, as JSON.
        sa.Column("facts", sa.Text),
        sa.Column("started_at", sa.DateTime, nullable=False),
        # Set by E10. The next run's E0 reads it: a run that completed
        # stands for a 3.0 that may have opened since (GV-4's audit event
        # migration.completed does not exist in 3.0 yet).
        sa.Column("completed_at", sa.DateTime),
        sa.Column("status", sa.String(32), nullable=False),
    )
    sa.Table(
        "id_map",
        metadata,
        sa.Column("entity", sa.String(64), primary_key=True),
        sa.Column("source_id", sa.Integer, primary_key=True),
        sa.Column("target_entity", sa.String(64), nullable=False),
        sa.Column("target_id", sa.Integer),
    )
    sa.Table(
        "dropped",
        metadata,
        sa.Column("entity", sa.String(64), primary_key=True),
        sa.Column("ref_id", sa.Integer, primary_key=True),
        sa.Column("reason", sa.String(64), nullable=False),
        sa.Column("detail", sa.Text),
    )
    sa.Table(
        "conflict",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("entity", sa.String(64), nullable=False),
        # What it is about, as text: an id, a DOI, an iD.
        sa.Column("ref", sa.String(512), nullable=False),
        # The source rows involved, as a JSON list of "table:id", and their
        # sha256: a decision taken on them holds while they stay the same
        # (§3.5).
        sa.Column("source_rows", sa.Text, nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("detail", sa.Text),
        # open, or decided by the decision named.
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("decision_id", sa.Integer),
    )
    sa.Table(
        "quarantine_description",
        metadata,
        sa.Column("ds_meta_data_id", sa.Integer, primary_key=True),
        sa.Column("original", sa.Text),
        sa.Column("sanitized", sa.Text),
    )
    sa.Table(
        "file_manifest",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("hubfile_id", sa.Integer),
        sa.Column("dataset_id", sa.Integer),
        # Where it was in v2.12's uploads/, and its key in the store.
        sa.Column("path", sa.String(1024), nullable=False),
        sa.Column("storage_key", sa.String(255)),
        sa.Column("checksum_algo", sa.String(16)),
        sa.Column("checksum", sa.String(120)),
        sa.Column("content_sha256", sa.String(64)),
        sa.Column("size", sa.BigInteger),
        sa.Column("status", sa.String(16), nullable=False),
    )
    sa.Table(
        "tombstone",
        metadata,
        sa.Column("doi", sa.String(120), primary_key=True),
        sa.Column("ds_meta_data_id", sa.Integer, nullable=False),
        # The withdrawn dataset whose landing answers its DOI (DM-4), NULL
        # when none is made.
        sa.Column("dataset_id", sa.Integer),
        # The metadata as they were, for the citation the tombstone shows.
        sa.Column("snapshot", sa.Text, nullable=False),
    )
    sa.Table(
        "usage_daily",
        metadata,
        # DM-5: v2.12's records by dataset or file, kind and day (E6).
        sa.Column("target_type", sa.String(16), primary_key=True),
        sa.Column("target_id", sa.Integer, primary_key=True),
        sa.Column("kind", sa.String(16), primary_key=True),
        sa.Column("day", sa.Date, primary_key=True),
        sa.Column("visitors", sa.Integer, nullable=False),
        sa.Column("records", sa.Integer, nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
    )
    sa.Table(
        "held_notice",
        metadata,
        # §5.5, §5.7: what each mail E6 holds in mail's outbox until RB-2
        # ends is about, and to whom, by the id of its outbox row.
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("outbox_id", sa.BigInteger, nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("ref", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer, nullable=False),
    )
    sa.Table(
        "takeover_candidate",
        metadata,
        sa.Column("reset_token_id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, nullable=False),
        # The address the link went to, as typed, and the account's.
        sa.Column("typed", sa.String(256), nullable=False),
        sa.Column("account_email", sa.String(256), nullable=False),
        sa.Column("issued_at", sa.DateTime),
        sa.Column("used_at", sa.DateTime),
        # probable (the link was followed) or attempt.
        sa.Column("kind", sa.String(16), nullable=False),
    )
    sa.Table(
        "profile",
        metadata,
        # P-00 to P-28 (§9.2): what each found, and the rule that handles it.
        sa.Column("name", sa.String(16), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("rule", sa.String(255)),
        sa.Column("found", sa.Integer, nullable=False),
        # The first rows found, as JSON.
        sa.Column("detail", sa.Text),
    )
    sa.Table(
        "counts",
        metadata,
        sa.Column("entity", sa.String(64), primary_key=True),
        sa.Column("source", sa.Integer),
        sa.Column("target", sa.Integer),
        sa.Column("dropped", sa.Integer),
        sa.Column("detail", sa.Text),
    )
    sa.Table(
        "verification",
        metadata,
        sa.Column("name", sa.String(64), primary_key=True),
        sa.Column("ok", sa.Boolean, nullable=False),
        sa.Column("blocking", sa.Boolean, nullable=False),
        sa.Column("detail", sa.Text),
    )
    return metadata


def _inputs(schema: str) -> sa.MetaData:
    metadata = sa.MetaData(schema=schema)
    sa.Table(
        "decision",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        # The conflict's kind, ref, source_rows and fingerprint, copied from
        # uvlhub_migration.conflict.
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("ref", sa.String(512), nullable=False),
        sa.Column("source_rows", sa.Text, nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("resolution", sa.String(64), nullable=False),
        sa.Column("note", sa.Text),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("decided_at", sa.DateTime, nullable=False),
    )
    sa.Table(
        "zenodo_snapshot",
        metadata,
        sa.Column("deposition_id", sa.Integer, primary_key=True),
        sa.Column("record", sa.Text, nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
    )
    sa.Table(
        "zenodo_files",
        metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("deposition_id", sa.Integer, nullable=False),
        sa.Column("name", sa.String(1024), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
    )
    sa.Table(
        "contract_collation",
        metadata,
        sa.Column("table_name", sa.String(64), primary_key=True),
        sa.Column("column_name", sa.String(64), primary_key=True),
        sa.Column("expected", sa.String(64), nullable=False),
    )
    return metadata


def create_outputs(connection, schema: str) -> dict[str, sa.Table]:
    """Drop and create the output schema (principle 3)."""
    connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {quote(schema)}")
    connection.exec_driver_sql(
        f"CREATE DATABASE {quote(schema)} CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"
    )
    metadata = _outputs(schema)
    metadata.create_all(connection)
    connection.commit()
    return {table.name: table for table in metadata.tables.values()}


def ensure_inputs(connection, schema: str) -> dict[str, sa.Table]:
    """The inputs schema, its tables created when missing, never dropped."""
    connection.exec_driver_sql(
        f"CREATE DATABASE IF NOT EXISTS {quote(schema)} "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"
    )
    metadata = _inputs(schema)
    metadata.create_all(connection, checkfirst=True)
    connection.commit()
    return {table.name: table for table in metadata.tables.values()}


def output_tables(schema: str) -> dict[str, sa.Table]:
    return {table.name: table for table in _outputs(schema).tables.values()}


def _jsonable(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    return str(value)


def to_json(value) -> str:
    return json.dumps(value, sort_keys=True, default=_jsonable, ensure_ascii=False)


def fingerprint(sources: dict[str, list]) -> str:
    """sha256 of the source rows a conflict or a decision is about, by
    table, in a form that does not depend on their order."""
    encoded = sorted(
        to_json({"table": table, "row": dict(row)})
        for table, rows in sources.items()
        for row in rows
    )
    return hashlib.sha256("\n".join(encoded).encode("utf-8")).hexdigest()


def source_refs(sources: dict[str, list]) -> list[str]:
    """The source rows of ``sources`` as "table:id", sorted: what E2 reads
    again to check a decision. E2's own findings name none."""
    return sorted(
        f"{table}:{row['id']}"
        for table, rows in sources.items()
        if table != SCHEMA
        for row in rows
    )


class Ledger:
    """What a run drops, maps and finds in conflict, kept until a stage
    writes it to the output schema."""

    def __init__(self):
        self.dropped: dict[tuple[str, int], dict] = {}
        self.id_map: dict[tuple[str, int], dict] = {}
        self.conflicts: list[dict] = []
        self.takeovers: list[dict] = []
        self.tombstones: list[dict] = []
        self.counts: dict[str, dict] = {}
        self.notes: Counter = Counter()
        # The decisions E2 found to hold, by (kind, ref); the ids of the
        # ones a conflict used; what a stage found that a decision was
        # taken on other rows than these.
        self.decisions: dict[tuple[str, str], dict] = {}
        self.used_decisions: set[int] = set()
        self.stale: list[str] = []

    def drop(self, entity: str, ref_id: int, reason: str, detail=None) -> None:
        # The first reason wins: a row dropped as seed stays seed even when
        # its owner is not loaded for that same reason.
        self.dropped.setdefault(
            (entity, int(ref_id)),
            {
                "entity": entity,
                "ref_id": int(ref_id),
                "reason": reason,
                "detail": None if detail is None else str(detail),
            },
        )

    def is_dropped(self, entity: str, ref_id) -> bool:
        return ref_id is not None and (entity, int(ref_id)) in self.dropped

    def reason(self, entity: str, ref_id, default: str) -> str:
        """Why ``entity`` ``ref_id`` was dropped, ``default`` if it was not."""
        entry = self.dropped.get((entity, int(ref_id))) if ref_id is not None else None
        return entry["reason"] if entry else default

    def owner_reason(self, user_id) -> str:
        """Why what belongs to account ``user_id`` is not loaded either: the
        account's own reason when it is the seed or held, else that its
        owner is not loaded, and orphan when there is no owner at all."""
        if user_id is None or ("user", int(user_id)) not in self.dropped:
            return ORPHAN
        reason = self.reason("user", user_id, OWNER_GONE)
        return reason if reason in (SEED, HELD) else OWNER_GONE

    def map(self, entity: str, source_id: int, target_entity: str, target_id) -> None:
        self.id_map[(entity, int(source_id))] = {
            "entity": entity,
            "source_id": int(source_id),
            "target_entity": target_entity,
            "target_id": None if target_id is None else int(target_id),
        }

    def conflict(self, kind: str, entity: str, ref, rows, detail=None) -> None:
        """A conflict of ``kind`` (CONFLICTS) about ``ref``. ``rows`` are the
        source rows it is about, whole, as all_rows reads them: of
        ``entity``'s table, or a mapping of table to rows when they are of
        several. A decision on the same rows closes it."""
        if kind not in CONFLICTS:
            raise KeyError(f"{kind}: a kind of conflict ledger.CONFLICTS does not name")
        sources = rows if isinstance(rows, dict) else {entity: rows}
        print_ = fingerprint(sources)
        status, decision_id = OPEN, None
        decision = self.decisions.get((kind, str(ref)))
        if decision is not None:
            if decision["fingerprint"] == print_:
                status, decision_id = DECIDED, decision["id"]
                self.used_decisions.add(decision["id"])
            else:
                self.stale.append(
                    f"decision {decision['id']} on {kind} {ref} was taken on "
                    "other rows than the source has now"
                )
        self.conflicts.append(
            {
                "kind": kind,
                "entity": entity,
                "ref": str(ref),
                "source_rows": to_json(source_refs(sources)),
                "fingerprint": print_,
                "detail": None if detail is None else str(detail),
                "status": status,
                "decision_id": decision_id,
            }
        )

    def open_conflicts(self) -> list[dict]:
        return [c for c in self.conflicts if c["status"] == OPEN]

    def note(self, what: str, how_many: int = 1) -> None:
        """Count something the report says (an ORCID set to NULL, a scope
        that went), which drops no row."""
        self.notes[what] += how_many

    def count(self, entity: str, source: int, target: int, detail=None) -> None:
        dropped = sum(1 for entity_, _ in self.dropped if entity_ == entity)
        self.counts[entity] = {
            "entity": entity,
            "source": source,
            "target": target,
            "dropped": dropped,
            "detail": None if detail is None else to_json(detail),
        }

    def write(self, connection, tables: dict[str, sa.Table]) -> None:
        """Replace what the output schema holds with what is here."""
        if connection.in_transaction():
            connection.commit()
        for name in (
            "dropped",
            "id_map",
            "conflict",
            "takeover_candidate",
            "tombstone",
            "counts",
        ):
            with connection.begin():
                connection.execute(tables[name].delete())
        insert_batches(
            connection, tables["dropped"], self.dropped.values(), key="ref_id"
        )
        insert_batches(
            connection, tables["id_map"], self.id_map.values(), key="source_id"
        )
        numbered = [
            dict(conflict, id=i) for i, conflict in enumerate(self.conflicts, 1)
        ]
        insert_batches(connection, tables["conflict"], numbered)
        insert_batches(
            connection,
            tables["takeover_candidate"],
            self.takeovers,
            key="reset_token_id",
        )
        insert_batches(
            connection, tables["tombstone"], self.tombstones, key="ds_meta_data_id"
        )
        insert_batches(connection, tables["counts"], self.counts.values(), key="entity")


def stop_on_conflicts(ctx, stage: str) -> None:
    """Stop the cutover at a conflict nobody has decided (§3.4); a
    rehearsal lists them in the report and goes on. A decision taken on
    other rows than the source has stops a rehearsal as well."""
    if ctx.ledger.stale:
        raise Refused(stage, ctx.ledger.stale)
    open_ = ctx.ledger.open_conflicts()
    if open_ and not ctx.params.allow_open_conflicts:
        kinds = Counter(conflict["kind"] for conflict in open_)
        raise Refused(
            stage,
            [
                f"{count} open conflict(s) of kind {kind}"
                for kind, count in sorted(kinds.items())
            ]
            + [
                "see uvlhub_migration.conflict; --allow-open-conflicts goes on (rehearsals)"
            ],
        )
