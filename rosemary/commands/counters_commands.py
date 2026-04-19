import click
from flask.cli import with_appcontext


@click.command(
    "counters:sync",
    help="Syncs all hub counters (datasets, feature models, views, downloads) from the database.",
)
@with_appcontext
def counters_sync():
    from app.modules.statistics.services import StatisticsService

    service = StatisticsService()

    try:
        statistics = service.refresh_statistics()

        click.echo(click.style("Hub counters synced successfully.", fg="green"))
        click.echo(f"  Datasets (synchronized):      {statistics.datasets_counter}")
        click.echo(f"  Feature models (synchronized):{statistics.feature_models_counter}")
        click.echo(f"  Dataset views:                {statistics.datasets_viewed}")
        click.echo(f"  Feature model views:          {statistics.feature_models_viewed}")
        click.echo(f"  Dataset downloads:            {statistics.datasets_downloaded}")
        click.echo(f"  Feature model downloads:      {statistics.feature_models_downloaded}")

    except Exception as e:
        click.echo(click.style(f"[ERROR] Failed to sync counters: {e}", fg="red"))
        raise
