import click
from flask.cli import with_appcontext
from app.modules.elasticsearch.utils import reindex_all


@click.command(
    "elasticsearch:reindex",
    help="Reindexes all datasets and hubfiles into the Elasticsearch index."
)
@with_appcontext
def elasticsearch_reindex():
    click.echo(click.style("[INFO] Starting reindexing process...", fg="cyan"))
    try:
        reindex_all()
        click.echo(click.style("[SUCCESS] Reindexing completed successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"[ERROR] Reindexing failed: {e}", fg="red"))
