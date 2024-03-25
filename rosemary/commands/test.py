import click
import subprocess
import os


@click.command('test', help="Runs pytest on the blueprints directory or a specific module.")
@click.argument('module_name', required=False)
def test(module_name):
    base_path = 'app/blueprints'
    test_path = base_path

    if module_name:
        test_path = os.path.join(base_path, module_name)
        if not os.path.exists(test_path):
            click.echo(click.style(f"Module '{module_name}' does not exist.", fg='red'))
            return
        click.echo(f"Running tests for the '{module_name}' module...")
    else:
        click.echo("Running tests for all modules...")

    try:
        subprocess.run(['pytest', '-v', test_path], check=True)
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error running tests: {e}", fg='red'))
