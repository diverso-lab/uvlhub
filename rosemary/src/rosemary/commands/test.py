"""``rosemary test`` — run the test suite at the framework's granularity.

Tests are tagged with pytest markers that match the splent testing pyramid::

    @pytest.mark.unit         pure logic, no Flask app, no DB
    @pytest.mark.repository   repository against the DB (no business logic)
    @pytest.mark.service      service-level with a real DB (orchestration + repos)
    @pytest.mark.integration  HTTP via Flask test client
    @pytest.mark.e2e          browser-driven end-to-end (selenium grid required)
    @pytest.mark.load         locust load tests (driven by ``rosemary locust``)

Each flag toggles one marker on. Combining flags ORs them. The default
(``rosemary test`` with no flag) runs unit + repository + service +
integration — the fast pyramid layers that don't depend on external infra.
"""
import os
import subprocess

import click

DEFAULT_MARKERS = ("unit", "repository", "service", "integration")


@click.command("test", help="Run pytest at the framework's granularity.")
@click.argument("feature", required=False)
@click.option("-k", "keyword", help="Only run tests matching the substring expression.")
@click.option("--unit", "selected", flag_value="unit", multiple=True,
              help="Pure unit tests (no app, no DB).")
@click.option("--repository", "selected", flag_value="repository", multiple=True,
              help="Repository tests against the database.")
@click.option("--service", "selected", flag_value="service", multiple=True,
              help="Service-level tests against the database.")
@click.option("--integration", "selected", flag_value="integration", multiple=True,
              help="HTTP integration tests via Flask test client.")
@click.option("--e2e", "selected", flag_value="e2e", multiple=True,
              help="Selenium end-to-end tests (requires the grid).")
@click.option("--all", "all_", is_flag=True,
              help="Shortcut for unit + repository + service + integration + e2e.")
@click.option("--load", "load_", is_flag=True,
              help="Forward to ``rosemary locust`` for load testing.")
def test(feature, keyword, selected, all_, load_):
    if load_:
        click.echo("Use ``rosemary locust`` (optionally with a feature name) for load tests.")
        return

    target = _resolve_target(feature)
    if target is None:
        return

    markers = _resolve_markers(selected, all_)
    cmd = ["pytest", "-v", target, "-m", " or ".join(markers)]
    if keyword:
        cmd += ["-k", keyword]

    click.echo(f"Running {' or '.join(markers)} tests against {target}...")
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
        # Click hands us a tuple via multiple=True; preserve order, drop dupes.
        seen, ordered = set(), []
        for marker in selected:
            if marker not in seen:
                seen.add(marker)
                ordered.append(marker)
        return tuple(ordered)
    return DEFAULT_MARKERS


if __name__ == "__main__":
    test()
