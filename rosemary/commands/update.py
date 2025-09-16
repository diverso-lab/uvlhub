import os
import subprocess

import click


def create_temp_requirements(requirements_path, temp_requirements_path):
    """Create a temporary requirements file without versions and handle editable sources."""
    editable_package = None
    with open(requirements_path, "r") as f, open(temp_requirements_path, "w") as temp_f:
        for line in f:
            if line.startswith("-e"):
                editable_package = line.strip()  # Store the editable package
            elif line.strip():
                package = line.split("==")[0].strip()  # Remove version information
                temp_f.write(package + "\n")
    return editable_package


def uninstall_packages():
    """Uninstall all non-editable packages."""
    installed_packages = subprocess.check_output(["pip", "freeze"]).decode("utf-8").splitlines()
    non_editable_packages = [pkg for pkg in installed_packages if not pkg.startswith("-e")]
    if non_editable_packages:
        subprocess.run(["pip", "uninstall", "-y"] + [pkg.split("==")[0] for pkg in non_editable_packages])


def install_packages(requirements_file):
    """Install packages from a requirements file."""
    subprocess.run(["pip", "install", "-r", requirements_file])


def regenerate_requirements(requirements_path):
    """Regenerate requirements.txt with resolved versions."""
    freeze_output = subprocess.check_output(["pip", "freeze"]).decode("utf-8")
    with open(requirements_path, "w") as f:
        f.write(freeze_output)


def reinstall_editable_package(editable_package):
    """Reinstall the editable package."""
    if editable_package:
        editable_path = editable_package.split()[1]  # Extract the path from '-e ./app'
        subprocess.run(
            ["pip", "install", "-e", editable_path],
            stdout=subprocess.DEVNULL,  # Suppress output
            stderr=subprocess.DEVNULL,  # Suppress errors
        )


def clean_up(temp_requirements_path):
    """Remove the temporary requirements file."""
    if os.path.exists(temp_requirements_path):
        os.remove(temp_requirements_path)


def update_pip():
    """Update pip dependencies."""
    requirements_path = os.path.join(os.getenv("WORKING_DIR", ""), "requirements.txt")
    temp_requirements_path = os.path.join(os.getenv("WORKING_DIR", ""), "temp_requirements.txt")

    editable_package = create_temp_requirements(requirements_path, temp_requirements_path)
    uninstall_packages()
    install_packages(temp_requirements_path)
    regenerate_requirements(requirements_path)
    reinstall_editable_package(editable_package)
    clean_up(temp_requirements_path)


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


@click.group()
def cli():
    """Manage updates for pip and npm dependencies."""


@cli.command()
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


@click.command("update:pip", help="Upload all pip dependencies.")
def update_pip_cmd():
    """Update only pip dependencies."""
    try:
        click.echo("Updating pip dependencies...")
        update_pip()
        click.echo(click.style("Pip dependencies updated successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error during pip update: {e}", fg="red"))


@click.command("update:npm", help="Upload all npm dependencies.")
def update_npm_cmd():
    """Update only npm dependencies."""
    try:
        click.echo("Updating npm dependencies...")
        update_npm()
        click.echo(click.style("NPM dependencies updated successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error during npm update: {e}", fg="red"))


if __name__ == "__main__":
    cli()
