"""``python -m uvlhub_splent.migration_v2``: the migrator's commands.

SPLENT has no command registry for a product (the CLI loads the features'
commands from the app), so the migrator is a module of the product run
with ``python -m``, in an ephemeral container of the 3.0 image (§3.4):

    python -m uvlhub_splent.migration_v2 grants            # SQL for the migrator account
    python -m uvlhub_splent.migration_v2 preflight ...     # E0 alone, touching nothing
    python -m uvlhub_splent.migration_v2 run ...           # E0 to E10
    python -m uvlhub_splent.migration_v2 contract [--check]

Passwords come from the environment only (MIGRATION_DB_PASSWORD,
MIGRATION_DB_ROOT_PASSWORD), never from the command line, which the
host's process list shows to anyone.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path

import click

from uvlhub_splent.migration_v2 import STAGES
from uvlhub_splent.migration_v2 import contract as contract_module
from uvlhub_splent.migration_v2.params import (
    Params,
    Refused,
    Server,
    parse_t0,
    split_list,
)

# The exit code of a run a stage refused, apart from click's 1 and 2.
REFUSED = 3


def _server_options(command):
    options = [
        click.option(
            "--db-host",
            envvar="MIGRATION_DB_HOST",
            required=True,
            help="The MariaDB server of the cutover.",
        ),
        click.option(
            "--db-port",
            envvar="MIGRATION_DB_PORT",
            type=int,
            default=3306,
            show_default=True,
        ),
        click.option(
            "--db-user",
            envvar="MIGRATION_DB_USER",
            default="migrator",
            show_default=True,
            help="The migrator account; its password is MIGRATION_DB_PASSWORD.",
        ),
        click.option(
            "--db-root-user",
            envvar="MIGRATION_DB_ROOT_USER",
            default="root",
            show_default=True,
            help="Restores the dump; its password is MIGRATION_DB_ROOT_PASSWORD.",
        ),
    ]
    for option in reversed(options):
        command = option(command)
    return command


def _run_options(command):
    options = [
        click.option(
            "--t0",
            envvar="MIGRATION_T0",
            required=True,
            help="The cutover's moment, ISO 8601, UTC.",
        ),
        click.option(
            "--expected-head",
            envvar="MIGRATION_EXPECTED_HEAD",
            required=True,
            help="The Alembic head of the v2.12 deployed.",
        ),
        click.option(
            "--admin-email",
            "admin_emails",
            multiple=True,
            envvar="MIGRATION_ADMIN_EMAILS",
            help="An account loaded as admin (DM-13). Repeat it, or a comma separated list.",
        ),
        click.option(
            "--dump",
            type=click.Path(path_type=Path),
            help="B1's logical dump of v2.12.",
        ),
        click.option(
            "--store-root",
            envvar="MIGRATION_STORE_ROOT",
            type=click.Path(path_type=Path),
            help="hubfile's store; the mirror of uploads/ is <store>/.legacy_mirror.",
        ),
        click.option(
            "--report",
            type=click.Path(path_type=Path),
            help="Where to write the report (JSON).",
        ),
        click.option(
            "--operator",
            envvar="MIGRATION_OPERATOR",
            default="",
            help="Who runs it, for the report.",
        ),
        click.option(
            "--force",
            is_flag=True,
            help="Run over a uvlhub3 that may have opened (needs --b2).",
        ),
        click.option(
            "--b2",
            type=click.Path(path_type=Path),
            help="The B2 taken in the last 15 minutes.",
        ),
        click.option(
            "--allow-open-conflicts",
            is_flag=True,
            help="Go on past open conflicts and list them (rehearsals only).",
        ),
        click.option(
            "--id-margin",
            envvar="MIGRATION_ID_MARGIN",
            type=int,
            default=1000,
            show_default=True,
        ),
        click.option("--ttl-write-days", type=int, default=90, show_default=True),
        click.option("--ttl-read-days", type=int, default=365, show_default=True),
        click.option(
            "--never-used-grace-days", type=int, default=30, show_default=True
        ),
        click.option("--unused-days", type=int, default=365, show_default=True),
        click.option("--ghost-draft-days", type=int, default=30, show_default=True),
        click.option(
            "--stages",
            default=",".join(STAGES),
            show_default=True,
            help="The stages to run, comma separated.",
        ),
    ]
    for option in reversed(options):
        command = option(command)
    return command


def _params(options: dict) -> Params:
    server = Server(
        host=options["db_host"],
        port=options["db_port"],
        user=options["db_user"],
        password=os.environ.get("MIGRATION_DB_PASSWORD", ""),
        root_user=options["db_root_user"],
        root_password=os.environ.get("MIGRATION_DB_ROOT_PASSWORD", ""),
    )
    stages = tuple(s.strip().upper() for s in options["stages"].split(",") if s.strip())
    unknown = [s for s in stages if s not in STAGES]
    if unknown:
        raise click.BadParameter(
            f"no such stage: {', '.join(unknown)}", param_hint="--stages"
        )
    return Params(
        server=server,
        t0=parse_t0(options["t0"]),
        expected_head=options["expected_head"],
        admin_emails=split_list(options["admin_emails"]),
        dump=options["dump"],
        store_root=options["store_root"],
        report=options["report"],
        operator=options["operator"],
        force=options["force"],
        b2=options["b2"],
        allow_open_conflicts=options["allow_open_conflicts"],
        id_margin=options["id_margin"],
        ttl_write_days=options["ttl_write_days"],
        ttl_read_days=options["ttl_read_days"],
        never_used_grace_days=options["never_used_grace_days"],
        unused_days=options["unused_days"],
        ghost_draft_days=options["ghost_draft_days"],
        stages=stages,
    )


def _refused(refusal: Refused) -> None:
    click.secho(f"{refusal.stage} refused:", fg="red", err=True)
    for reason in refusal.reasons:
        click.echo(f"  {reason}", err=True)
    sys.exit(REFUSED)


@click.group()
def main():
    """The migrator of uvlhub.io 2.12 into uvlhub 3.0 (CO-3)."""


@main.command()
@_server_options
@_run_options
def run(**options):
    """Run the migration, E0 to E10, and write the report."""
    from uvlhub_splent.migration_v2.pipeline import run as run_pipeline

    params = _params(options)
    try:
        report = run_pipeline(params)
    except Refused as refusal:
        _refused(refusal)
    click.secho(
        f"Done: stages {', '.join(report['stages_run'])}; "
        f"{sum(report['conflicts'].values())} open conflict(s); "
        f"ready for the cutover: {report['ready_for_cutover']}.",
        fg="green",
    )


@main.command()
@_server_options
@_run_options
def preflight(**options):
    """Run E0 alone: the safeguards, without touching any schema."""
    from uvlhub_splent.migration_v2.pipeline import Context
    from uvlhub_splent.migration_v2.preflight import preflight as check

    ctx = Context(_params(options))
    try:
        check(ctx)
    except Refused as refusal:
        _refused(refusal)
    finally:
        ctx.close()
    click.secho("E0: nothing stops the run.", fg="green")


@main.command()
@click.option("--user", default="migrator", show_default=True)
@click.option(
    "--host",
    "account_host",
    default="%",
    show_default=True,
    help="Where the account may connect from.",
)
def grants(user, account_host):
    """Print the SQL that creates the migrator account, for root to run.

    The account is made for the cutover and dropped when it ends (§3.4):
    everything on uvlhub3, the source, the clean v2.12 E2 compares it with
    and the work schemas, nothing else.
    """
    params = Params(server=Server(host=""), t0=parse_t0("1970-01-01"), expected_head="")
    password = secrets.token_urlsafe(24)
    click.echo(f"-- MIGRATION_DB_PASSWORD={password}")
    click.echo("\n".join(grant_statements(params, user, account_host, password)))


def grant_statements(params: Params, user: str, host: str, password: str) -> list[str]:
    account = f"'{user}'@'{host}'"
    statements = [f"CREATE USER {account} IDENTIFIED BY '{password}';"]
    for schema in (
        params.target_schema,
        params.source_schema,
        params.reference_schema,
        params.work_schema,
        params.inputs_schema,
    ):
        statements.append(f"GRANT ALL PRIVILEGES ON `{schema}`.* TO {account};")
    return statements


@main.command("contract")
@click.option(
    "--check",
    "check_host",
    default=None,
    help="Compare uvlhub3 on this server with it.",
)
@click.option("--db-port", type=int, default=3306)
@click.option("--db-user", default="migrator")
@click.option("--schema", default="uvlhub3")
def contract_command(check_host, db_port, db_user, schema):
    """Say what the data contract holds, or compare a uvlhub3 with it."""
    contract = contract_module.load()
    if check_host is None:
        summary = {
            "version": contract.version,
            "database": f"{contract.charset} {contract.collation}",
            "tables": {
                role: sorted(t.name for t in contract.by_role(role))
                for role in (
                    contract_module.LOAD,
                    contract_module.READ,
                    contract_module.EMPTY,
                )
            },
            "dm15_pending": contract.dm15_pending(),
            "versions": contract_module.version_differences(contract),
        }
        click.echo(json.dumps(summary, indent=2))
        return
    from uvlhub_splent.migration_v2.db import make_engine

    engine = make_engine(
        check_host, db_port, db_user, os.environ.get("MIGRATION_DB_PASSWORD", "")
    )
    with engine.connect() as connection:
        found = contract_module.differences(
            contract, contract_module.schema_columns(connection, schema)
        )
    engine.dispose()
    for line in found:
        click.echo(line)
    sys.exit(1 if found else 0)
