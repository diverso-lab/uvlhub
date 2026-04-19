import click
from flask.cli import with_appcontext


@click.command(
    "statistics:refresh",
    help="Recalculates persisted hub statistics from record tables.",
)
@with_appcontext
def statistics_refresh():
    from app.modules.statistics.services import StatisticsService

    service = StatisticsService()

    try:
        statistics = service.refresh_statistics()

        click.echo(click.style("Statistics refreshed successfully.", fg="green"))
        click.echo(f"Dataset views: {statistics.datasets_viewed}")
        click.echo(f"Model views: {statistics.feature_models_viewed}")
        click.echo(f"Dataset downloads: {statistics.datasets_downloaded}")
        click.echo(f"Model downloads: {statistics.feature_models_downloaded}")

    except Exception as e:
        click.echo(click.style(f"[ERROR] Failed to refresh statistics: {e}", fg="red"))
