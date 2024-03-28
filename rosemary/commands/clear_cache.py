import click
import shutil
import os


@click.command('clear:cache', help="Clears pytest cache in app/blueprints and the build directory at the root.")
def clear_cache():

    if click.confirm('Are you sure you want to clear the pytest cache and the build directory?'):

        pytest_cache_dir = '/app/app/blueprints/.pytest_cache'
        build_dir = '/app/build'

        if os.path.exists(pytest_cache_dir):
            try:
                shutil.rmtree(pytest_cache_dir)
                click.echo(click.style("Pytest cache cleared.", fg='green'))
            except Exception as e:
                click.echo(click.style(f"Failed to clear pytest cache: {e}", fg='red'))
        else:
            click.echo(click.style("No pytest cache found. Nothing to clear.", fg='yellow'))

        if os.path.exists(build_dir):
            try:
                shutil.rmtree(build_dir)
                click.echo(click.style("Build directory cleared.", fg='green'))
            except Exception as e:
                click.echo(click.style(f"Failed to clear build directory: {e}", fg='red'))
        else:
            click.echo(click.style("No cache or build directory found. Nothing to clear.", fg='yellow'))
    else:
        click.echo(click.style("Clear operation cancelled.", fg='yellow'))

# No olvides registrar este comando en tu CLI, como lo has hecho con los otros comandos.
