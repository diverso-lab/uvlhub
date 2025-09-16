import click
from flask.cli import with_appcontext

from core.managers.module_manager import ModuleManager


@click.command("module:list", help="Lists all modules and those ignored by .moduleignore.")
@with_appcontext
def module_list():
    app = click.get_current_context().obj
    manager = ModuleManager(app)

    loaded_modules, ignored_modules = manager.get_modules()

    click.echo(click.style(f"Loaded Modules ({len(loaded_modules)}):", fg="green"))
    for module in loaded_modules:
        click.echo(f"- {module}")

    click.echo(click.style(f"\nIgnored Modules ({len(ignored_modules)}):", fg="bright_yellow"))
    for module in ignored_modules:
        click.echo(click.style(f"- {module}", fg="bright_yellow"))
