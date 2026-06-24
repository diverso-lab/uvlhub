import json
import os
import subprocess
import sys

import click


def resolve_base_path(specified_path):
    base_path = specified_path or os.getenv("WORKING_DIR", "")
    if os.path.exists(base_path):
        return base_path

    relative = os.path.join(".", base_path)
    if os.path.exists(relative):
        return relative

    raise FileNotFoundError(f"Paths '{base_path}' and '{relative}' do not exist.")


def build_detect_secrets_cmd(path, baseline_file, all_files, baseline):
    cmd = [
        "detect-secrets",
        "-C",
        path,
        "scan",
        "--exclude-files",
        baseline_file,
    ]

    if all_files:
        cmd.append("--all-files")

    if baseline:
        cmd.extend(["--baseline", baseline_file])

    return cmd


def run_scan(cmd, write_to=None):
    if write_to:
        with open(write_to, "w") as file:
            subprocess.run(cmd, stdout=file, check=True)
        return None

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def parse_results(raw_output):
    data = json.loads(raw_output)
    return data.get("results", {})


def render_results(secrets, baseline_file, show_hash):
    if not secrets:
        click.echo(click.style("No secrets found!", fg="green"))
        sys.exit(0)

    contains_real = False

    for file, entries in secrets.items():
        for entry in entries:
            if not entry.get("is_secret", True):
                continue

            contains_real = True
            line = entry["line_number"]

            click.echo(
                click.style(
                    f"{file}:{line}",
                    fg="yellow",
                )
            )

            if show_hash:
                click.echo(
                    click.style(
                        f"  Hashed: {entry['hashed_secret']}",
                        fg="red",
                    )
                )

    if contains_real:
        click.echo(
            click.style(
                "Secrets detected.",
                fg="red",
            )
        )
        click.echo(
            click.style(
                f"Run 'detect-secrets audit {baseline_file}' " "to review false positives.",
                fg="cyan",
            )
        )
        sys.exit(1)

    click.echo(
        click.style(
            "All secrets are managed in baseline.",
            fg="green",
        )
    )
    sys.exit(0)


@click.command("detect_secrets")
@click.argument("specified_path", required=False)
@click.option("--all-files", is_flag=True)
@click.option("--baseline", is_flag=True)
@click.option("--add-to-baseline", is_flag=True)
@click.option(
    "--show-hash",
    is_flag=True,
    help="Display hashed secrets in output.",
)
def detect_secrets(
    specified_path,
    all_files,
    baseline,
    add_to_baseline,
    show_hash,
):
    try:
        base_path = resolve_base_path(specified_path)
    except FileNotFoundError as e:
        click.echo(click.style(str(e), fg="red"))
        sys.exit(1)

    baseline_file = os.path.join(base_path, ".secrets.baseline")

    cmd = build_detect_secrets_cmd(
        base_path,
        baseline_file,
        all_files,
        baseline,
    )

    try:
        if add_to_baseline:
            run_scan(cmd, write_to=baseline_file)
            click.echo(click.style("Baseline updated.", fg="green"))
            sys.exit(0)

        raw_output = run_scan(cmd)
        secrets = parse_results(raw_output)
        render_results(
            secrets,
            baseline_file,
            show_hash,
        )

    except subprocess.CalledProcessError as e:
        click.echo(
            click.style(
                f"Error running detect-secrets: {e}",
                fg="red",
            )
        )
        sys.exit(1)
