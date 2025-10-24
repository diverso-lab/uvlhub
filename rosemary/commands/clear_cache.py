import os
import shutil
from pathlib import Path

import click


@click.command(
    "clear:cache",
    help="Clears pytest cache in app/modules and the build directory at the root.",
)
def clear_cache():

    if click.confirm("Are you sure you want to clear the pytest cache and the build directory?"):

        project_root = Path(os.getenv("WORKING_DIR", ""))
        pytest_cache_dir = os.path.join(os.getenv("WORKING_DIR", ""), "app/modules/.pytest_cache")
        build_dir = os.path.join(os.getenv("WORKING_DIR", ""), "build")

        if os.path.exists(pytest_cache_dir):
            try:
                shutil.rmtree(pytest_cache_dir)
                click.echo(click.style("Pytest cache cleared.", fg="green"))
            except Exception as e:
                click.echo(click.style(f"Failed to clear pytest cache: {e}", fg="red"))
        else:
            click.echo(click.style("No pytest cache found. Nothing to clear.", fg="yellow"))

        if os.path.exists(build_dir):
            try:
                shutil.rmtree(build_dir)
                click.echo(click.style("Build directory cleared.", fg="green"))
            except Exception as e:
                click.echo(click.style(f"Failed to clear build directory: {e}", fg="red"))
        else:
            click.echo(click.style("No cache or build directory found. Nothing to clear.", fg="yellow"))

        pycache_dirs = project_root.rglob("__pycache__")
        for dir in pycache_dirs:
            try:
                shutil.rmtree(dir)
            except Exception as e:
                click.echo(click.style(f"Failed to clear __pycache__ directory {dir}: {e}", fg="red"))
        click.echo(click.style("All __pycache__ directories cleared.", fg="green"))

        pyc_files = project_root.rglob("*.pyc")
        for file in pyc_files:
            try:
                file.unlink()
            except Exception as e:
                click.echo(click.style(f"Failed to clear .pyc file {file}: {e}", fg="red"))

        click.echo(click.style("All cache cleared.", fg="green"))

    else:
        click.echo(click.style("Clear operation cancelled.", fg="yellow"))
