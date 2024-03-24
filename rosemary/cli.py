# rosemary/cli.py

import click
from rosemary.commands.update import update
from rosemary.commands.info import info
from rosemary.commands.make_module import make_module


@click.group()
def cli():
    pass


cli.add_command(update)
cli.add_command(info)
cli.add_command(make_module)

if __name__ == '__main__':
    cli()
