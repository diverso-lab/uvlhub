import click

from .clear_cache import clear_cache
from .clear_log import clear_log
from .clear_uploads import clear_uploads


@click.command("clear:all", help="Clears cache, uploads and log files.")
@click.pass_context
def clear_all(ctx):
    """Run all clear commands in sequence."""
    click.echo(click.style("🚀 Running all clear commands...", fg="cyan"))

    ctx.invoke(clear_cache)
    ctx.invoke(clear_uploads)
    ctx.invoke(clear_log)

    click.echo(click.style("✨ All clear commands executed successfully!", fg="green"))
