import os
import shutil
import subprocess

import click
from flask.cli import with_appcontext
from sqlalchemy import MetaData

from app import create_app, db
from rosemary.commands.clear_uploads import clear_uploads


@click.command(
    "db:reset",
    help="Resets the database, optionally clears migrations and recreates them.",
)
@click.option(
    "--clear-migrations",
    is_flag=True,
    help="Remove all tables including 'alembic_version', clear migrations folder, and recreate migrations.",
)
@click.option("-y", "--yes", is_flag=True, help="Confirm the operation without prompting.")
@with_appcontext
def db_reset(clear_migrations, yes):
    app = create_app()
    with app.app_context():
        if not yes and not click.confirm(
            "WARNING: This will delete all data and clear uploads. Are you sure?",
            abort=True,
        ):
            return

        # Deletes data from all tables
        try:
            meta = MetaData()
            meta.reflect(bind=db.engine)
            with db.engine.connect() as conn:
                trans = conn.begin()  # Begin transaction
                for table in reversed(meta.sorted_tables):
                    if not clear_migrations or table.name != "alembic_version":
                        conn.execute(table.delete())
                trans.commit()  # End transaction
            click.echo(click.style("All table data cleared.", fg="yellow"))
            subprocess.run(["flask", "db", "stamp", "head"], check=True)
        except Exception as e:
            click.echo(click.style(f"Error clearing table data: {e}", fg="red"))
            if trans:
                trans.rollback()
            return

        # Delete the uploads folder
        ctx = click.get_current_context()
        ctx.invoke(clear_uploads)

        if clear_migrations:
            # Delete the migration folder if it exists.
            migrations_dir = os.path.join(os.getenv("WORKING_DIR", ""), "migrations")
            if os.path.isdir(migrations_dir):
                shutil.rmtree(migrations_dir)
                click.echo(click.style("Migrations directory cleared.", fg="yellow"))

            # Run flask db init, migrate and upgrade
            try:
                subprocess.run(["flask", "db", "init"], check=True)
                subprocess.run(["flask", "db", "migrate"], check=True)
                subprocess.run(["flask", "db", "upgrade"], check=True)
                click.echo(click.style("Database recreated from new migrations.", fg="green"))
            except subprocess.CalledProcessError as e:
                click.echo(click.style(f"Error during migrations reset: {e}", fg="red"))
                return

        click.echo(click.style("Database reset successfully.", fg="green"))
