import os
import subprocess
import sys

import click


@click.command(
    "linter",
    help="Runs flake8 + black --check + isort --check-only on 'app', 'rosemary' and 'core' "
    "(same checks as .github/workflows/CI_lint.yml).",
)
def linter():

    # Mirror the CI Python Lint job exactly: flake8, black --check and
    # isort --check-only, all three pointed at the same three directories.
    # Running them locally via `rosemary linter` used to only cover flake8,
    # so PRs kept bouncing off the black/isort steps after being green
    # locally — fixed by running the full triad here.
    working_dir = os.getenv("WORKING_DIR", "")
    directories = [
        os.path.join(working_dir, "app"),
        os.path.join(working_dir, "rosemary"),
        os.path.join(working_dir, "core"),
    ]

    checks = [
        ("flake8", ["flake8", *directories]),
        ("black --check", ["black", "--check", *directories]),
        ("isort --check-only", ["isort", "--check-only", *directories]),
    ]

    failed = []
    for label, cmd in checks:
        click.echo(click.style(f"\n==> {label}", fg="cyan"))
        result = subprocess.run(cmd)
        if result.returncode != 0:
            click.echo(click.style(f"{label} found issues.", fg="red"))
            failed.append(label)
        else:
            click.echo(click.style(f"{label}: clean.", fg="green"))

    if failed:
        click.echo(
            click.style(
                "\nFailed: " + ", ".join(failed) + ". Run `rosemary linter:fix` to auto-format.",
                fg="red",
            )
        )
        sys.exit(1)
    click.echo(click.style("\nAll lint checks passed. Congratulations!", fg="green"))


@click.command(
    "linter:fix",
    help="Automatically formats and cleans code in 'app', 'rosemary', and 'core' directories.",
)
def linter_fix():
    import os
    import subprocess

    import click

    working_dir = os.getenv("WORKING_DIR", "")
    directories = [
        os.path.join(working_dir, "app"),
        os.path.join(working_dir, "rosemary"),
        os.path.join(working_dir, "core"),
    ]

    for directory in directories:
        click.echo(click.style(f"\nProcessing {directory}...", fg="cyan"))

        # 1. Remove unused imports & variables
        subprocess.run(
            [
                "autoflake",
                "--in-place",
                "--remove-unused-variables",
                "--remove-all-unused-imports",
                "--recursive",
                directory,
            ]
        )

        # 2. Sort imports
        subprocess.run(["isort", directory])

        # 3. Format code with Black
        result = subprocess.run(["black", "--line-length=120", directory])

        if result.returncode != 0:
            click.echo(click.style(f"Failed on {directory}", fg="red"))
        else:
            click.echo(click.style(f"✔ {directory} cleaned & formatted", fg="green"))
