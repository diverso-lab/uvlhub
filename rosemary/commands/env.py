# rosemary/commands/env.py

import click
from dotenv import dotenv_values


@click.command()
def env():
    """Displays the current .env file values."""
    # Load the .env file
    env_values = dotenv_values(".env")

    # Display keys and values
    for key, value in env_values.items():
        click.echo(f"{key}={value}")
