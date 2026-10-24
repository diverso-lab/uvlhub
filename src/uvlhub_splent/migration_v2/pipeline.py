"""The run: every stage in order, with what they share (§3.4).

E0 takes the lock and keeps it to the end. Once the outputs exist (right
after E0), every stage's ledger is written there and the report is written
whatever happens: a refusal leaves as much to read as a success.
"""

from __future__ import annotations

import time
from dataclasses import asdict

import sqlalchemy as sa

from uvlhub_splent.migration_v2 import MIGRATOR_VERSION, NOT_YET
from uvlhub_splent.migration_v2 import contract as contract_module
from uvlhub_splent.migration_v2.content import content
from uvlhub_splent.migration_v2.db import make_engine
from uvlhub_splent.migration_v2.files import files
from uvlhub_splent.migration_v2.identity import identity
from uvlhub_splent.migration_v2.ledger import (
    Ledger,
    create_outputs,
    ensure_inputs,
    to_json,
)
from uvlhub_splent.migration_v2.params import Params, Refused
from uvlhub_splent.migration_v2.preflight import preflight, release_lock
from uvlhub_splent.migration_v2.report import finish
from uvlhub_splent.migration_v2.restore import restore
from uvlhub_splent.migration_v2.schema import build_schema
from uvlhub_splent.migration_v2.verify import post_load


class Context:
    """What the stages of one run share."""

    def __init__(self, params: Params, contract=None):
        self.params = params
        self.contract = contract or contract_module.load()
        server = params.server
        self.engine = make_engine(
            server.host, server.port, server.user, server.password
        )
        self.root = make_engine(
            server.host, server.port, server.root_user, server.root_password
        )
        self.lock = None
        self.ledger = Ledger()
        self.facts: dict = {}
        self.checks: list = []
        self.loaded: dict[str, set] = {}
        self.published: set = set()
        self.takeover_users: set = set()
        self.source_counters: dict = {}
        self.stages_done: list[str] = []
        self.outputs = None
        self.inputs = None
        self.run_id = None

    def close(self) -> None:
        release_lock(self.lock)
        self.lock = None
        self.engine.dispose()
        self.root.dispose()


def _open_run(ctx) -> None:
    """The outputs made again, and the run's row."""
    params = ctx.params
    with ctx.engine.connect() as connection:
        ctx.outputs = create_outputs(connection, params.work_schema)
        ctx.inputs = ensure_inputs(connection, params.inputs_schema)
        facts = {
            "params": {
                key: str(value)
                for key, value in asdict(params).items()
                if key != "server"
            },
            "server": {
                "host": params.server.host,
                "port": params.server.port,
                "user": params.server.user,
            },
            "features": {
                name: contract_module.installed_version(name)
                for name in ctx.contract.features
            },
        }
        ctx.facts.update(facts)
        with connection.begin():
            result = connection.execute(
                ctx.outputs["run"]
                .insert()
                .values(
                    migrator_version=MIGRATOR_VERSION,
                    contract_version=ctx.contract.version,
                    t0=params.t0,
                    operator=params.operator,
                    dump=str(params.dump) if params.dump else None,
                    facts=to_json(facts),
                    started_at=sa.func.utc_timestamp(),
                    status="running",
                )
            )
        ctx.run_id = result.inserted_primary_key[0]


STAGE_FUNCTIONS = {
    "E1": restore,
    "E3": build_schema,
    "E4": identity,
    "E5": content,
    "E7": post_load,
    "E8": files,
}


def run(params: Params, contract=None) -> dict:
    """Run the stages ``params.stages`` names. Answers the report; raises
    Refused, after writing it, when a stage stops the run. Any other error
    is written down as the stage's stop as well, then raised as it is."""
    ctx = Context(params, contract)
    stopped = crash = None
    stage = "E0"
    try:
        started = time.monotonic()
        preflight(ctx)
        ctx.stages_done.append("E0")
        _open_run(ctx)
        timings = {"E0": round(time.monotonic() - started, 3)}
        ctx.facts["timings"] = timings
        for stage in params.stages:
            if stage in ("E0", "E10") or stage in NOT_YET:
                continue
            started = time.monotonic()
            STAGE_FUNCTIONS[stage](ctx)
            timings[stage] = round(time.monotonic() - started, 3)
            ctx.stages_done.append(stage)
        stage = "E10"
        ctx.stages_done.append("E10")
    except Refused as refusal:
        stopped = refusal
    except Exception as error:  # written down, then raised as it is
        crash = error
        stopped = Refused(stage, f"{type(error).__name__}: {error}")
    try:
        report = finish(ctx, stopped)
    except Exception:
        # A crash that left the server unreachable cannot be written down
        # either; the crash is what the operator needs to see.
        if crash is None:
            raise
        report = None
    finally:
        ctx.close()
    if crash is not None:
        raise crash
    if stopped is not None:
        stopped.report = report
        raise stopped
    return report
