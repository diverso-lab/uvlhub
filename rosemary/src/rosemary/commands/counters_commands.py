import click
from flask.cli import with_appcontext

# Fields printed by the sync output, in the order we want them to appear.
# Keys match `Statistics` model columns so the same list drives both the
# live sync and the --dry-run diff.
_FIELDS = [
    ("datasets_counter", "Datasets (DOI-synced)"),
    ("feature_models_counter", "Feature models (DOI-synced)"),
    ("datasets_viewed", "Dataset views"),
    ("feature_models_viewed", "Feature model views"),
    ("datasets_downloaded", "Dataset downloads"),
    ("feature_models_downloaded", "Feature model downloads"),
]


def _format_diff(before: int, after: int) -> str:
    delta = after - before
    if delta == 0:
        return click.style(f"{after}", fg="white")
    arrow = click.style(f"{before} → {after}", fg="yellow")
    colour = "green" if delta > 0 else "red"
    sign = "+" if delta > 0 else ""
    return f"{arrow} ({click.style(f'{sign}{delta}', fg=colour)})"


@click.command(
    "counters:sync",
    help=(
        "Recompute hub counters (datasets, feature models, views, downloads) "
        "from the record tables. Use --dry-run to preview drift without "
        "writing; the dashboard cache is invalidated on a successful commit."
    ),
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would change without touching the Statistics row or cache.",
)
@with_appcontext
def counters_sync(dry_run: bool):
    from app.features.statistics.services import DashboardService, StatisticsService

    service = StatisticsService()

    try:
        diff = service.preview_refresh()

        if dry_run:
            click.echo(click.style("Dry-run — no changes persisted.", fg="cyan"))
        else:
            service.refresh_statistics()
            # Drop the cached dashboard so the next hit reflects the new totals.
            try:
                DashboardService().invalidate_cache()
            except Exception as exc:  # pragma: no cover — best-effort cleanup
                click.echo(click.style(f"[WARN] Dashboard cache invalidate failed: {exc}", fg="yellow"))
            click.echo(click.style("Hub counters synced successfully.", fg="green"))

        any_changes = any(before != after for before, after in diff.values())
        if any_changes:
            click.echo()
        for field, label in _FIELDS:
            before, after = diff.get(field, (0, 0))
            click.echo(f"  {label:<30} {_format_diff(before, after)}")

    except Exception as e:
        click.echo(click.style(f"[ERROR] Failed to sync counters: {e}", fg="red"))
        raise
