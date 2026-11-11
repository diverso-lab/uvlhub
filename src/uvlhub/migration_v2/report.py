"""E10, the report: what a run loaded, dropped and left open (§3.4).

Written as JSON wherever --report says, and in uvlhub_migration.run, also
when a stage stopped the run, so a refusal can be read as well as a
success. The run's row gets completed_at only when every stage went
through: that is what the next run's E0 reads as migration.completed.

``ready_for_cutover`` is True only for a run with nothing pending: no stage
skipped or stopped, no open conflict, no blocking check failed, E5 a final
pass with nothing deferred (content.FIRST_PASS, content.DEFERRED), and
SECRET_KEY checked to be another than v2.12's (DM-1, E0). E9's checks do
not count: what they make is made again once 3.0 is up, and the alerts say
which. The report is signed with the operator's name and the sha256 of its
own content; a real signature (GPG, the operator's key) is the runbook's.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter

import sqlalchemy as sa

from uvlhub.migration_v2 import MIGRATOR_VERSION, NOT_YET
from uvlhub.migration_v2.content import DEFERRED, FIRST_PASS
from uvlhub.migration_v2.db import insert_batches
from uvlhub.migration_v2.ledger import DECIDED, to_json

# What the stages this version does not have would need (MIG-01, MIG-06,
# MIG-07, MIG-11), for the report to say.
LATER: dict[str, str] = {}
# The conflicts about accounts, whose ref may be an address or an iD: the
# report names their rows instead, which uvlhub_migration.conflict pairs
# with the ref.
PERSONAL = ("email_", "identity_")


def conflict_detail(conflict: dict) -> dict:
    """A conflict as the report lists it: what it is, about which rows, and
    what the stage that raised it says, without personal data."""
    personal = conflict["kind"].startswith(PERSONAL)
    return {
        "kind": conflict["kind"],
        "entity": conflict["entity"],
        "ref": None if personal else conflict["ref"],
        "source_rows": json.loads(conflict["source_rows"]),
        "detail": None if personal else conflict["detail"],
        "status": conflict["status"],
    }


def build(ctx, stopped=None) -> dict:
    ledger = ctx.ledger
    dropped = Counter(
        (entry["entity"], entry["reason"]) for entry in ledger.dropped.values()
    )
    open_conflicts = ledger.open_conflicts()
    failed = [c.name for c in ctx.checks if c.blocking and not c.ok]
    report = {
        "migrator_version": MIGRATOR_VERSION,
        "contract_version": ctx.contract.version,
        "operator": ctx.params.operator,
        "t0": ctx.params.t0,
        "expected_head": ctx.params.expected_head,
        "stages_run": ctx.stages_done,
        "stages_not_yet": {stage: LATER[stage] for stage in NOT_YET},
        "stopped": None
        if stopped is None
        else {"stage": stopped.stage, "reasons": stopped.reasons},
        "e5_first_pass": {"first_pass": FIRST_PASS, "deferred": list(DEFERRED)},
        "facts": ctx.facts,
        "counts": list(ledger.counts.values()),
        "dropped": [
            {"entity": entity, "reason": reason, "rows": rows}
            for (entity, reason), rows in sorted(dropped.items())
        ],
        "conflicts": {
            kind: count
            for kind, count in sorted(
                Counter(c["kind"] for c in open_conflicts).items()
            )
        },
        # Every conflict, open or decided, so the report can be read
        # without the output schema (which goes with the server).
        "conflict_detail": [conflict_detail(c) for c in ledger.conflicts],
        "decided": {
            kind: count
            for kind, count in sorted(
                Counter(
                    c["kind"] for c in ledger.conflicts if c["status"] == DECIDED
                ).items()
            )
        },
        "decisions": {
            "holding": sorted(d["id"] for d in ledger.decisions.values()),
            "unused": sorted(
                d["id"]
                for d in ledger.decisions.values()
                if d["id"] not in ledger.used_decisions
            ),
        },
        "profile": ctx.facts.get("profile", {}),
        "legacy": ctx.facts.get("legacy", {}),
        "alerts": ctx.alerts,
        "dm5": ctx.facts.get("dm5"),
        "takeover_candidates": Counter(t["kind"] for t in ledger.takeovers),
        "tombstones": len(ledger.tombstones),
        "notes": dict(sorted(ledger.notes.items())),
        "checks": [check.as_row() for check in ctx.checks],
        "dm15_pending": ctx.contract.dm15_pending(),
    }
    report["dm1"] = ctx.facts.get("dm1", {"rotation_checked": False})
    report["ready_for_cutover"] = bool(
        stopped is None
        and not NOT_YET
        and not open_conflicts
        and not failed
        and not report["e5_first_pass"]["first_pass"]
        and not report["e5_first_pass"]["deferred"]
        and report["dm1"]["rotation_checked"]
    )
    body = to_json(report)
    report["signature"] = {
        "operator": ctx.params.operator,
        "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }
    return report


def finish(ctx, stopped=None) -> dict:
    """Write the report and the run's row. The row is completed only when no
    stage stopped the run."""
    report = build(ctx, stopped)
    if ctx.params.report is not None:
        ctx.params.report.parent.mkdir(parents=True, exist_ok=True)
        ctx.params.report.write_text(
            json.dumps(json.loads(to_json(report)), indent=2, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
    if ctx.outputs is not None:
        with ctx.engine.connect() as connection:
            ctx.ledger.write(connection, ctx.outputs)
            verification = ctx.outputs["verification"]
            with connection.begin():
                connection.execute(verification.delete())
            insert_batches(
                connection, verification, [c.as_row() for c in ctx.checks], key="name"
            )
            with connection.begin():
                connection.execute(
                    ctx.outputs["run"]
                    .update()
                    .where(ctx.outputs["run"].c.id == ctx.run_id)
                    .values(
                        facts=to_json(ctx.facts),
                        dump_sha256=ctx.facts.get("dump_sha256"),
                        source_head=ctx.facts.get("source_head"),
                        status="stopped " + stopped.stage if stopped else "completed",
                        completed_at=sa.func.utc_timestamp()
                        if stopped is None
                        else None,
                    )
                )
    return report
