import subprocess

import click
from flask.cli import with_appcontext


@click.command("db:migrate", help="Generates and applies database migrations.")
@with_appcontext
def db_migrate():
    # Generates migrations
    click.echo("Generating database migrations...")
    result_migrate = subprocess.run(["flask", "db", "migrate"])
    if result_migrate.returncode == 0:
        click.echo(click.style("Migrations generated successfully.", fg="green"))
    else:
        click.echo(
            click.style(
                "Note: No new migrations needed or an error occurred " "while generating migrations.",
                fg="yellow",
            )
        )

    # Applies to migrations
    click.echo("Applying database migrations...")
    result_upgrade = subprocess.run(["flask", "db", "upgrade"])
    if result_upgrade.returncode == 0:
        click.echo(click.style("Migrations applied successfully.", fg="green"))
    else:
        click.echo(
            click.style(
                "Error applying migrations. This may be due to the database " "being already up-to-date.",
                fg="yellow",
            )
        )
