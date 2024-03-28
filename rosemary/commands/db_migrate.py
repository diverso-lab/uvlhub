import click
import subprocess
from flask.cli import with_appcontext


@click.command('db:migrate', help="Generates and applies database migrations.")
@with_appcontext
def db_migrate():
    # Generates migrations
    try:
        click.echo("Generating database migrations...")
        subprocess.run(['flask', 'db', 'migrate'], check=True)
        click.echo(click.style("Migrations generated successfully.", fg='green'))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error generating migrations: {e}", fg='red'))
        return

    # Applies to migrations
    try:
        click.echo("Applying database migrations...")
        subprocess.run(['flask', 'db', 'upgrade'], check=True)
        click.echo(click.style("Migrations applied successfully.", fg='green'))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error applying migrations: {e}", fg='red'))
        return
