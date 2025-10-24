# rosemary/commands/env.py

import os

import click
from dotenv import dotenv_values


@click.command()
def env():
    """Displays the current .env file values."""
    # Load the .env file
    env_values = dotenv_values(os.path.join(os.getenv("WORKING_DIR", ""), ".env"))

    # Display keys and values
    for key, value in env_values.items():
        click.echo(f"{key}={value}")
