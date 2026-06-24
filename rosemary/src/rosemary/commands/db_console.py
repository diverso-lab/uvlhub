import os
import subprocess

import click
from dotenv import load_dotenv


@click.command("db:console", help="Opens a MariaDB console with credentials from .env.")
def db_console():
    load_dotenv()

    mariadb_hostname = os.getenv("MARIADB_HOSTNAME")
    mariadb_user = os.getenv("MARIADB_USER")
    mariadb_password = os.getenv("MARIADB_PASSWORD")
    mariadb_database = os.getenv("MARIADB_DATABASE")

    # Build the command to connect to MariaDB
    mariadb_connect_cmd = f"mysql -h{mariadb_hostname} -u{mariadb_user} -p{mariadb_password} {mariadb_database}"

    # Execute the command
    try:
        subprocess.run(mariadb_connect_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error opening MariaDB console: {e}", fg="red"))
