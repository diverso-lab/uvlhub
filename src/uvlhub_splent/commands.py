"""The product's own commands, ``splent product:<name>`` (CLI 1.42.0).

``product:migrate-v2`` is the migrator of uvlhub.io 2.12 (docs/migration_v2.md)
with the CLI's conveniences: the commands of
``python -m uvlhub_splent.migration_v2``, under one group. The CLI runs it
in the product's app, whose engine may keep pooled connections to the
server, and E0 refuses a server with connections that are not the
migrator's. So before anything runs, the app's session gives its
connection back and every engine of the app is disposed; a connection
something still holds refuses the command. The cutover keeps
``python -m uvlhub_splent.migration_v2``, which builds no app at all.
"""

import click

from uvlhub_splent.migration_v2.cli import main as migrator


def release_app_connections() -> None:
    """Close every connection the app's engines keep. Raises
    click.ClickException when one is still in use, since E0 would count it
    as somebody else's."""
    from splent_framework.db import db

    db.session.remove()
    for engine in db.engines.values():
        held = engine.pool.checkedout()
        if held:
            raise click.ClickException(
                f"the app holds {held} connection(s) to "
                f"{engine.url.host or engine.url.database}; "
                "run python -m uvlhub_splent.migration_v2 instead"
            )
        engine.dispose()


@click.group("migrate-v2")
def migrate_v2():
    """The migrator of uvlhub.io 2.12 (python -m uvlhub_splent.migration_v2)."""
    release_app_connections()


for _command in migrator.commands.values():
    migrate_v2.add_command(_command)

cli_commands = [migrate_v2]
