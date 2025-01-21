import click
import os
import subprocess


@click.command()
def update():
    """Update dependencies by cleaning and regenerating requirements.txt, while handling editable sources separately."""
    requirements_path = os.path.join(os.getenv("WORKING_DIR", ""), "requirements.txt")
    temp_requirements_path = os.path.join(os.getenv("WORKING_DIR", ""), "temp_requirements.txt")
    editable_package = None  # To store the editable package if present

    try:
        # Step 1: Create a temporary requirements file without versions and editable sources
        with open(requirements_path, "r") as f, open(temp_requirements_path, "w") as temp_f:
            for line in f:
                if line.startswith("-e"):
                    editable_package = line.strip()  # Store the editable package
                elif line.strip():
                    package = line.split("==")[0].strip()  # Remove version information
                    temp_f.write(package + "\n")

        # Step 2: Uninstall all non-editable packages
        installed_packages = subprocess.check_output(["pip", "freeze"]).decode("utf-8").splitlines()
        non_editable_packages = [pkg for pkg in installed_packages if not pkg.startswith("-e")]
        if non_editable_packages:
            subprocess.check_call(["pip", "uninstall", "-y"] + [pkg.split("==")[0] for pkg in non_editable_packages])

        # Step 3: Install packages from the temporary requirements file
        subprocess.check_call(["pip", "install", "-r", temp_requirements_path])

        # Step 4: Regenerate requirements.txt with resolved versions
        freeze_output = subprocess.check_output(["pip", "freeze"]).decode("utf-8")
        with open(requirements_path, "w") as f:
            f.write(freeze_output)

        # Step 5: Reinstall the editable package, suppressing any output or errors
        if editable_package:
            editable_path = editable_package.split()[1]  # Extract the path from '-e ./app'
            subprocess.run(
                ["pip", "install", "-e", editable_path],
                stdout=subprocess.DEVNULL,  # Suppress output
                stderr=subprocess.DEVNULL,  # Suppress errors
            )

        # Clean up the temporary file
        os.remove(temp_requirements_path)

        click.echo(click.style("Update completed successfully!", fg="green"))

    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"Error during the update: {e}", fg="red"))
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {e}", fg="red"))


if __name__ == "__main__":
    update()
