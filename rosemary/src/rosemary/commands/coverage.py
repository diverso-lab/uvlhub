"""``rosemary coverage`` — pytest with coverage at the framework's granularity.

Same flag surface as ``rosemary test``: pick which markers run and the
coverage report covers exactly what those tests exercise. ``--html`` also
emits an htmlcov/ tree at the workspace root.
"""

import os
import subprocess

import click

DEFAULT_MARKERS = ("unit", "repository", "service", "integration")


@click.command("coverage", help="Run pytest with coverage at the framework's granularity.")
@click.argument("feature", required=False)
@click.option("-k", "keyword", help="Only run tests matching the substring expression.")
@click.option("--unit", "selected", flag_value="unit", multiple=True, help="Pure unit tests (no app, no DB).")
@click.option(
    "--repository", "selected", flag_value="repository", multiple=True, help="Repository tests against the database."
)
@click.option(
    "--service", "selected", flag_value="service", multiple=True, help="Service-level tests against the database."
)
@click.option(
    "--integration",
    "selected",
    flag_value="integration",
    multiple=True,
    help="HTTP integration tests via Flask test client.",
)
@click.option(
    "--e2e", "selected", flag_value="e2e", multiple=True, help="Selenium end-to-end tests (requires the grid)."
)
@click.option("--all", "all_", is_flag=True, help="Shortcut for unit + repository + service + integration + e2e.")
@click.option("--html", is_flag=True, help="Also write an HTML report to htmlcov/.")
def coverage(feature, keyword, selected, all_, html):
    target = _resolve_target(feature)
    if target is None:
        return

    markers = _resolve_markers(selected, all_)
    cmd = [
        "pytest",
        target,
        "--cov=" + target,
        "--cov-report=term-missing",
        "-m",
        " or ".join(markers),
    ]
    if html:
        cmd += ["--cov-report=html"]
    if keyword:
        cmd += ["-k", keyword]

    click.echo(f"Coverage for {' or '.join(markers)} tests against {target}...")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"pytest failed: {e}", fg="red"))


def _resolve_target(feature):
    working_dir = os.getenv("WORKING_DIR", "")
    features_dir = os.path.join(working_dir, "app/features")
    if not feature:
        return features_dir
    target = os.path.join(features_dir, feature)
    if not os.path.isdir(target):
        click.echo(click.style(f"Feature '{feature}' does not exist.", fg="red"))
        return None
    return target


def _resolve_markers(selected, all_):
    if all_:
        return ("unit", "repository", "service", "integration", "e2e")
    if selected:
        seen, ordered = set(), []
        for marker in selected:
            if marker not in seen:
                seen.add(marker)
                ordered.append(marker)
        return tuple(ordered)
    return DEFAULT_MARKERS


if __name__ == "__main__":
    coverage()
