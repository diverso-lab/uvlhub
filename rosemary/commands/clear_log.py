import glob
import os

import click


@click.command("clear:log", help="Clears all 'app.log' files (including rotated ones).")
def clear_log():
    workdir = os.getenv("WORKING_DIR", "")
    log_pattern = os.path.join(workdir, "app.log*")
    log_files = glob.glob(log_pattern)

    if not log_files:
        click.echo(click.style("No 'app.log' files found.", fg="yellow"))
        return

    deleted = 0
    for log_file in log_files:
        try:
            os.remove(log_file)
            deleted += 1
        except Exception as e:
            click.echo(click.style(f"Error deleting '{log_file}': {e}", fg="red"))

    if deleted > 0:
        click.echo(click.style(f"✅ Deleted {deleted} log file(s).", fg="green"))
