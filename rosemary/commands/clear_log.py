import os

import click


@click.command("clear:log", help="Clears the 'app.log' file.")
def clear_log():
    log_file_path = os.path.join(os.getenv("WORKING_DIR", ""), "app.log")

    # Check if the log file exists
    if os.path.exists(log_file_path):
        try:
            # Deletes the log file
            os.remove(log_file_path)
            click.echo(click.style("The 'app.log' file has been successfully cleared.", fg="green"))
        except Exception as e:
            click.echo(click.style(f"Error clearing the 'app.log' file: {e}", fg="red"))
    else:
        click.echo(click.style("The 'app.log' file does not exist.", fg="yellow"))
