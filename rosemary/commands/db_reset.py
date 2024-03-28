import click
from flask.cli import with_appcontext
from app import db
from sqlalchemy import MetaData
from flask_migrate import upgrade
from rosemary.commands.clear_uploads import clear_uploads


@click.command('db:reset', help="Drops all tables except 'alembic_version', then recreates them from migrations, "
                                "and clears the uploads directory.")
@with_appcontext
def db_reset():
    if not click.confirm('WARNING: This will delete all data except migration data and clear uploads. Are you sure?',
                         abort=True):
        return

    try:
        meta = MetaData()
        meta.reflect(bind=db.engine)
        with db.engine.connect() as conn:
            trans = conn.begin()  # Initiate a transaction
            for table in reversed(meta.sorted_tables):
                if table.name != 'alembic_version':
                    conn.execute(table.delete())
            trans.commit()  # Transaction Commit
        click.echo(click.style("All table data cleared except 'alembic_version'.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"Error clearing table data: {e}", fg='red'))
        if trans:
            trans.rollback()
        return

    # Invoke the clear:uploads command
    ctx = click.get_current_context()
    ctx.invoke(clear_uploads)

    # Recreate the tables and execute the migrations
    try:
        upgrade()
        click.echo(click.style("Tables recreated from migrations.", fg='green'))
    except Exception as e:
        click.echo(click.style(f"Error recreating tables from migrations: {e}", fg='red'))
