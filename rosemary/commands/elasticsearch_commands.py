import click
from flask.cli import with_appcontext
from app.modules.elasticsearch.utils import reindex_all
from app.modules.elasticsearch.services import ElasticsearchService


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


@click.command(
    "elasticsearch:reset",
    help="Deletes and recreates the Elasticsearch index, then reindexes all documents."
)
@with_appcontext
def elasticsearch_reset():
    search = ElasticsearchService()
    try:
        click.echo(click.style("🗑️  Deleting Elasticsearch index...", fg="yellow"))
        search.es.indices.delete(index=search.index_name)
        click.echo(click.style("✅ Index deleted successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"⚠️  Could not delete index: {e}", fg="bright_yellow"))

    try:
        click.echo(click.style("📦 Recreating Elasticsearch index...", fg="cyan"))
        search.create_index_if_not_exists()
        click.echo(click.style("✅ Index created successfully.", fg="green"))
    except Exception as e:
        click.echo(click.style(f"[ERROR] Failed to create index: {e}", fg="red"))
        return

    try:
        click.echo(click.style("🔁 Reindexing all documents...", fg="cyan"))
        reindex_all()
        click.echo(click.style("✅ Reindexing completed successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"[ERROR] Reindexing failed: {e}", fg="red"))
