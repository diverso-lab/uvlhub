import os
import subprocess

import click


@click.command(
    "coverage",
    help="Runs pytest coverage on the blueprints directory or a specific module.",
)
@click.argument("module_name", required=False)
@click.option("--html", is_flag=True, help="Generates an HTML coverage report.")
def coverage(module_name, html):
    base_path = os.path.join(os.getenv("WORKING_DIR", ""), "app/modules")
    test_path = base_path

    if module_name:
        test_path = os.path.join(base_path, module_name)
        if not os.path.exists(test_path):
            click.echo(click.style(f"Module '{module_name}' does not exist.", fg="red"))
            return
        click.echo(f"Running coverage for the '{module_name}' module...")
    else:
        click.echo("Running coverage for all modules...")

    coverage_cmd = [
        "pytest",
        "--ignore-glob=*selenium*",
        "--cov=" + test_path,
        test_path,
    ]

    if html:
        coverage_cmd.extend(["--cov-report", "html"])

    try:
        subprocess.run(coverage_cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error running coverage: {e}", fg="red"))
