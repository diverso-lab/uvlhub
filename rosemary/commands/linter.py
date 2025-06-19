import click
import os
import subprocess


@click.command(
    "linter", help="Runs flake8 linter on the 'app' and 'rosemary' directories."
)
def linter():

    # Define the directories to be checked with flake8
    working_dir = os.getenv("WORKING_DIR", "")
    directories = [
        os.path.join(working_dir, "app"),
        os.path.join(working_dir, "rosemary"),
        os.path.join(working_dir, "core"),
    ]

    # Run flake8 in each directory
    for directory in directories:
        click.echo(f"Running flake8 on {directory}...")
        result = subprocess.run(["flake8", directory])

        # Check if flake8 encountered problems
        if result.returncode != 0:
            click.echo(click.style(f"flake8 found issues in {directory}.", fg="red"))
        else:
            click.echo(
                click.style(
                    f"No issues found in {directory}. Congratulations!", fg="green"
                )
            )


@click.command(
    "linter:fix",
    help="Automatically formats code in 'app', 'rosemary', and 'core' directories using black.",
)
def linter_fix():

    # Define the directories to be formatted
    working_dir = os.getenv("WORKING_DIR", "")
    directories = [
        os.path.join(working_dir, "app"),
        os.path.join(working_dir, "rosemary"),
        os.path.join(working_dir, "core"),
    ]

    # Run black to format the code
    for directory in directories:
        click.echo(f"Running black on {directory}...")
        result = subprocess.run(["black", directory])

        # Check if black encountered problems
        if result.returncode != 0:
            click.echo(
                click.style(f"Failed to format {directory} with black.", fg="red")
            )
        else:
            click.echo(
                click.style(f"Code in {directory} formatted successfully!", fg="green")
            )
