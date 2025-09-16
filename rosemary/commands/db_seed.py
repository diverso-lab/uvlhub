import importlib
import inspect
import os

import click
from flask.cli import with_appcontext

from core.seeders.BaseSeeder import BaseSeeder
from rosemary.commands.db_reset import db_reset


def get_module_seeders(module_path, specific_module=None):
    seeders = []
    for root, dirs, files in os.walk(module_path):
        if "seeders.py" in files:
            relative_path = os.path.relpath(root, module_path)
            module_name = relative_path.replace(os.path.sep, ".")
            full_module_name = f"app.modules.{module_name}.seeders"

            # If a module was specified and does not match the current one, continue with the next one
            if specific_module and specific_module != module_name.split(".")[0]:
                continue

            seeder_module = importlib.import_module(full_module_name)
            importlib.reload(seeder_module)  # Reload the module

            for attr in dir(seeder_module):
                potential_seeder_class = getattr(seeder_module, attr)
                if (
                    inspect.isclass(potential_seeder_class)
                    and issubclass(potential_seeder_class, BaseSeeder)
                    and potential_seeder_class is not BaseSeeder
                ):
                    seeders.append(potential_seeder_class())

    # Sort seeders by priority
    seeders.sort(key=lambda seeder: seeder.priority)

    return seeders


@click.command("db:seed", help="Populates the database with the seeders defined in each module.")
@click.option("--reset", is_flag=True, help="Reset the database before seeding.")
@click.option("-y", "--yes", is_flag=True, help="Confirm the operation without prompting.")
@click.argument("module", required=False)
@with_appcontext
def db_seed(reset, yes, module):

    if reset:
        if yes or click.confirm(
            click.style("This will reset the database, do you want " "to continue?", fg="red"),
            abort=True,
        ):
            click.echo(click.style("Resetting the database...", fg="yellow"))
            ctx = click.get_current_context()
            ctx.invoke(db_reset, clear_migrations=False, yes=True)
        else:
            click.echo(click.style("Database reset cancelled.", fg="yellow"))
            return

    blueprints_module_path = os.path.join(os.getenv("WORKING_DIR", ""), "app/modules")
    seeders = get_module_seeders(blueprints_module_path, specific_module=module)
    success = True  # Flag to control the successful flow of the operation

    if module:
        click.echo(click.style(f"Seeding data for the '{module}' module...", fg="green"))
    else:
        click.echo(click.style("Seeding data for all modules...", fg="green"))

    for seeder in seeders:
        try:
            seeder.run()
            click.echo(click.style(f"{seeder.__class__.__name__} performed.", fg="blue"))
        except Exception as e:
            click.echo(click.style(f"Error running seeder {seeder.__class__.__name__}: {e}", fg="red"))
            click.echo(
                click.style(
                    f"Rolled back the transaction of {seeder.__class__.__name__} to keep the session " f"clean.",
                    fg="yellow",
                )
            )

            success = False
            break

    if success:
        click.echo(click.style("Database populated with test data.", fg="green"))
