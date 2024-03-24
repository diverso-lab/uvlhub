# rosemary/cli.py

import click
from rosemary.commands.update import update
from rosemary.commands.info import info
from rosemary.commands.env import env


@click.group()
def cli():
    pass


cli.add_command(update)
cli.add_command(info)
cli.add_command(env)

if __name__ == '__main__':
    cli()
