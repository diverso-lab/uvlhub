import importlib
import os

import click


class RosemaryCLI(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = super().get_command(ctx, cmd_name)
        if rv is None:
            click.echo(f"No such command '{cmd_name}'.")
            click.echo("Try 'rosemary --help' for a list of available commands.")
        return rv


@click.group(cls=RosemaryCLI)
def cli():
    """A CLI tool to help with project development."""


# Automatically discover and load commands
def load_commands(cli_group):
    """
    Dynamically import all command modules in rosemary.commands and add their
    click.Command attributes to the CLI group.
    """
    commands_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commands")
    for file in os.listdir(commands_path):
        if file.endswith(".py") and not file.startswith("__"):
            module_name = f"rosemary.commands.{file[:-3]}"
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, click.Command):
                    cli_group.add_command(attr)


# Load commands dynamically
load_commands(cli)

if __name__ == "__main__":
    cli()
