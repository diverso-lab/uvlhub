import os
import subprocess
from datetime import datetime

import click
from dotenv import load_dotenv


@click.command("db:dump", help="Creates a MariaDB SQL dump using credentials from .env.")
@click.option(
    "--output",
    "-o",
    help="Output file path. Defaults to db_dump_<timestamp>.sql",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite output file if it already exists.",
)
def db_dump(output, force):
    load_dotenv()

    mariadb_hostname = os.getenv("MARIADB_HOSTNAME")
    mariadb_user = os.getenv("MARIADB_USER")
    mariadb_password = os.getenv("MARIADB_PASSWORD")
    mariadb_database = os.getenv("MARIADB_DATABASE")

    if not all([mariadb_hostname, mariadb_user, mariadb_password, mariadb_database]):
        click.echo(click.style("Missing MariaDB configuration in .env", fg="red"))
        return

    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"db_dump_{mariadb_database}_{timestamp}.sql"

    if os.path.exists(output) and not force:
        click.echo(click.style(f"File already exists: {output}", fg="red"))
        click.echo("Use --force to overwrite.")
        return

    dump_cmd = (
        f"mysqldump "
        f"-h{mariadb_hostname} "
        f"-u{mariadb_user} "
        f"-p{mariadb_password} "
        f"--single-transaction "
        f"--routines "
        f"--triggers "
        f"{mariadb_database} > {output}"
    )

    click.echo(f"Creating database dump: {output}")

    try:
        subprocess.run(dump_cmd, shell=True, check=True)
        click.echo(click.style("Database dump created successfully.", fg="green"))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error creating database dump: {e}", fg="red"))
