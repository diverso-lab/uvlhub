import os
import shutil

import click

from core.configuration.configuration import uploads_folder_name


@click.command(
    "clear:uploads",
    help="Clears the contents of the 'uploads' directory without removing the folder.",
)
def clear_uploads():
    uploads_dir = os.path.join(os.getenv("WORKING_DIR", ""), uploads_folder_name())

    # Verify if the 'uploads' folder exists
    if os.path.exists(uploads_dir) and os.path.isdir(uploads_dir):
        try:
            # Iterate over the contents of the directory
            for filename in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, filename)

                # If it's a file, remove it
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.remove(file_path)
                # If it's a directory, remove it and its contents
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

            click.echo(
                click.style(
                    "The contents of the 'uploads' directory have been successfully cleared.",
                    fg="green",
                )
            )
        except Exception as e:
            click.echo(click.style(f"Error clearing the 'uploads' directory: {e}", fg="red"))
    else:
        click.echo(click.style("The 'uploads' directory does not exist.", fg="yellow"))
