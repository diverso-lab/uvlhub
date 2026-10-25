"""E9, derived: what 3.0 makes from its data, made again (§7, DM-6).

None of it is migrated. v2.12's FactLabels carry neither sanitising nor
provenance and miss the models over 64 KB (A10-10); its formats are files
uvl makes again (UV-4); its index held absolute URLs and unsanitised
descriptions, and was exposed without authentication (§7.1). Once the files
are in the store (E8), E9 runs the features' own commands, each in a
process of its own, as E3 and E8 do, so their writes go through their ORM
there and never in this process:

- factlabel: ``splent feature:factlabel generate`` computes every FactLabel
  (hubfile_factlabel, which E7 found empty), then ``metrics-backfill
  --force`` makes each file's metrics from it, in the place of the legacy
  ones E5 copied (§7.3); a file whose FactLabel cannot be computed keeps
  those;
- formats: ``splent feature:uvl generate``, the Glencoe, DIMACS and SPLOT
  files of every UVL model, into the store (§7.4);
- reindex: ``splent feature:explore reset``, the search index made again
  from uvlhub3 (DC-4, §7.1).

E9 never stops the run (§3.4): a command that fails is an alert in the
report and a check that does not block, explore answers with its SQL
fallback meanwhile, and what is left is done after the opening with the
same command (§9.3, 4:05). ``--derived`` says which run: the cutover may
leave FactLabel and formats to after the opening, as the plan's day does.
"""

from __future__ import annotations

import os
import subprocess

import sqlalchemy as sa
from splent_io.splent_feature_hubfile.storage import DATASETS

from uvlhub_splent.migration_v2 import DERIVED
from uvlhub_splent.migration_v2.db import qualified
from uvlhub_splent.migration_v2.schema import child_env
from uvlhub_splent.migration_v2.verify import Check

# The tables of the load E9 writes again: their rows carry the moment they
# were made, so they are not the same from one run to the next (principle 2
# holds for what the migrator writes).
REWRITTEN = ("hubfile_metrics",)
# What the store keeps a file's derived formats under (hubfile's
# derived_key: datasets/<id>/derived/<hubfile_id>/<format>).
DERIVED_FOLDER = "derived"


def commands(params) -> dict[str, list[tuple[str, ...]]]:
    return {
        "factlabel": list(params.factlabel_commands),
        "formats": [params.formats_command],
        "reindex": [params.reindex_command],
    }


def run_command(command, env) -> tuple[bool, list[str]]:
    """Run a feature's command; whether it went through, and the tail of
    what it said."""
    result = subprocess.run(
        list(command),
        env=env,
        cwd=env.get("WORKING_DIR") or None,
        capture_output=True,
        text=True,
        check=False,
    )
    output = ((result.stdout or "") + (result.stderr or "")).strip().splitlines()
    return result.returncode == 0, output[-15:]


def made(ctx) -> dict:
    """What 3.0 has of what E9 makes, once it ran."""
    target = ctx.params.target_schema
    with ctx.engine.connect() as connection:
        files, labels, metrics = connection.execute(
            sa.text(
                f"SELECT (SELECT COUNT(*) FROM {qualified(target, 'hubfiles')}), "
                f"(SELECT COUNT(*) FROM {qualified(target, 'hubfile_factlabel')} "
                " WHERE factlabel_json IS NOT NULL AND factlabel_json <> ''), "
                f"(SELECT COUNT(*) FROM {qualified(target, 'hubfile_metrics')})"
            )
        ).one()
        connection.rollback()
    formats = 0
    root = ctx.params.store_root
    if root is not None and (root / DATASETS).is_dir():
        for folder, _dirs, names in os.walk(root / DATASETS):
            if f"/{DERIVED_FOLDER}/" in f"{folder}/":
                formats += len(names)
    return {
        "hubfiles": files,
        "factlabels": labels,
        "metrics": metrics,
        "format_files": formats,
    }


def derived(ctx) -> None:
    params = ctx.params
    env = child_env(
        params,
        **(
            {"HUBFILE_STORAGE_ROOT": str(params.store_root)}
            if params.store_root
            else {}
        ),
    )
    plan = commands(params)
    outcome = {}
    for name in DERIVED:
        if name not in params.derived:
            outcome[name] = {"ran": False}
            continue
        ok, said = True, []
        for command in plan[name]:
            ok, said = run_command(command, env)
            if not ok:
                break
        outcome[name] = {"ran": True, "ok": ok, "output": said}
        ctx.checks.append(
            Check(
                f"E9-{name}",
                ok,
                blocking=False,
                detail=None if ok else {"command": " ".join(command), "output": said},
            )
        )
        if not ok:
            ctx.alerts.append(
                f"E9 {name}: {' '.join(command)} failed; run it again once 3.0 "
                "is up"
                + (
                    "; explore answers with its SQL fallback"
                    if name == "reindex"
                    else ""
                )
            )
    ctx.facts["derived"] = {"commands": outcome, "made": made(ctx)}
