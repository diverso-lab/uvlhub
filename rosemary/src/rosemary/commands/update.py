import os
import re
import subprocess
import tomllib

import click


def _pyproject_path():
    return os.path.join(os.getenv("WORKING_DIR", ""), "pyproject.toml")


def _declared_dependencies(pyproject_path):
    """Return the raw [project.dependencies] entries from pyproject.toml."""
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    return data.get("project", {}).get("dependencies", [])


def _write_dependencies(pyproject_path, new_deps):
    """Replace the [project.dependencies] array in pyproject.toml in place."""
    with open(pyproject_path, "r", encoding="utf-8") as f:
        text = f.read()
    block = "dependencies = [\n" + "".join(f'    "{d}",\n' for d in new_deps) + "]"
    new_text = re.sub(r"dependencies = \[.*?\]", block, text, count=1, flags=re.DOTALL)
    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(new_text)


def _frozen_versions():
    frozen = subprocess.check_output(["pip", "freeze"]).decode("utf-8").splitlines()
    versions = {}
    for line in frozen:
        if "==" in line and not line.startswith("-e"):
            name, ver = line.split("==", 1)
            versions[name.lower()] = ver.strip()
    return versions


def update_pip():
    """Upgrade the declared pip dependencies and refresh their pinned versions in pyproject.toml."""
    pyproject_path = _pyproject_path()
    deps = _declared_dependencies(pyproject_path)
    names = [re.split(r"[=<>!~ ]", d, 1)[0].strip() for d in deps if d.strip()]

    if names:
        subprocess.run(["pip", "install", "--upgrade", "--pre", *names], check=False)

    versions = _frozen_versions()
    new_deps = [f"{n}=={versions[n.lower()]}" if n.lower() in versions else n for n in names]
    _write_dependencies(pyproject_path, new_deps)


def update_npm():
    """Update npm dependencies."""
    working_dir = os.getenv("WORKING_DIR", "")
    package_json_path = os.path.join(working_dir, "package.json")

    if not os.path.exists(package_json_path):
        click.echo(click.style("No package.json found. Skipping npm update.", fg="yellow"))
        return

    try:
        # Step 1: Update package.json to latest versions
        subprocess.run(["npx", "npm-check-updates", "-u"], cwd=working_dir)

        # Step 2: Install updated dependencies
        subprocess.run(["npm", "install"], cwd=working_dir)

        click.echo(click.style("NPM dependencies updated successfully!", fg="green"))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error during npm update: {e}", fg="red"))


@click.command("update", help="Update both pip (pyproject.toml) and npm dependencies.")
def update():
    """Update both pip and npm dependencies."""
    try:
        click.echo("Updating pip dependencies...")
        update_pip()
        click.echo("Updating npm dependencies...")
        update_npm()
        click.echo(click.style("All dependencies updated successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error during update: {e}", fg="red"))


@click.command("update:pip", help="Upgrade pip dependencies and re-pin them in pyproject.toml.")
def update_pip_cmd():
    """Update only pip dependencies."""
    try:
        click.echo("Updating pip dependencies...")
        update_pip()
        click.echo(click.style("Pip dependencies updated successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error during pip update: {e}", fg="red"))


@click.command("update:npm", help="Update all npm dependencies.")
def update_npm_cmd():
    """Update only npm dependencies."""
    try:
        click.echo("Updating npm dependencies...")
        update_npm()
        click.echo(click.style("NPM dependencies updated successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error during npm update: {e}", fg="red"))
