import click
from flask.cli import with_appcontext

from rosemary.commands.counters_commands import counters_sync


@click.command(
    "statistics:refresh",
    help=(
        "DEPRECATED alias for `counters:sync`. Will be removed next release — "
        "use `rosemary counters:sync` (optionally with --dry-run) instead."
    ),
    context_settings={"ignore_unknown_options": True},
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Forwarded to `counters:sync --dry-run`.",
)
@click.pass_context
@with_appcontext
def statistics_refresh(ctx, dry_run: bool):
    click.echo(
        click.style(
            "DEPRECATED: `statistics:refresh` has been renamed to `counters:sync`. "
            "This alias will be removed next release.",
            fg="yellow",
        )
    )
    ctx.invoke(counters_sync, dry_run=dry_run)
