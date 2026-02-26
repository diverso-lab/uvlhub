import os
import subprocess

import click


@click.command("test", help="Runs pytest on the blueprints directory or a specific module.")
@click.argument("module_name", required=False)
@click.option("-k", "keyword", help="Only run tests that match the given substring expression.")
def test(module_name, keyword):
    base_path = os.path.join(os.getenv("WORKING_DIR", ""), "app/modules")
    test_path = base_path

    if module_name:
        test_path = os.path.join(base_path, module_name)
        if not os.path.exists(test_path):
            click.echo(click.style(f"Module '{module_name}' does not exist.", fg="red"))
            return
        click.echo(f"Running tests for the '{module_name}' module...")
    else:
        click.echo("Running tests for all modules...")

    pytest_cmd = ["pytest", "-v", "--ignore-glob=*selenium*", test_path]

    if keyword:
        pytest_cmd.extend(["-k", keyword])

    try:
        subprocess.run(pytest_cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error running tests: {e}", fg="red"))


if __name__ == "__main__":
    test()
