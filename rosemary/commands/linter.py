import click
import subprocess


@click.command('linter', help="Runs flake8 linter on the 'app' and 'rosemary' directories.")
def linter():

    # Define the directories to be checked with flake8
    directories = ["/app/app", "/app/rosemary"]

    # Run flake8 in each directory
    for directory in directories:
        click.echo(f"Running flake8 on {directory}...")
        result = subprocess.run(['flake8', directory])

        # Check if flake8 encountered problems
        if result.returncode != 0:
            click.echo(click.style(f"flake8 found issues in {directory}.", fg='red'))
        else:
            click.echo(click.style(f"No issues found in {directory}. Congratulations!", fg='green'))
