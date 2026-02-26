import os
import signal
import subprocess

import click
import psutil

import docker


@click.command("locust", help="Launches Locust for load testing based on the environment.")
@click.argument("module", required=False)
def locust(module):

    # Absolute paths
    working_dir = os.getenv("WORKING_DIR", "")
    core_dir = os.path.join(working_dir, "core")
    docker_dir = os.path.join(working_dir, "docker/")
    modules_dir = os.path.join(working_dir, "app/modules")

    def validate_module(module):
        """Check if the module exists."""
        if module:
            module_path = os.path.join(modules_dir, module)
            if not os.path.exists(module_path):
                raise click.UsageError(f"module '{module}' does not exist.")
            locustfile_path = os.path.join(module_path, "tests", "locustfile.py")
            if not os.path.exists(locustfile_path):
                raise click.UsageError(
                    f"Locustfile for module '{module}' does not exist at path " f"'{locustfile_path}'."
                )

    def run_docker_locust(volume_name, module):
        """Build and run the Locust container with the specified volume."""

        try:
            # Check if the container already exists
            client.containers.get("locust_container")
            click.echo("Locust container is already running.")
            return
        except docker.errors.NotFound:
            pass  # Container does not exist, proceed to create it

        click.echo(f"Starting Locust in Docker environment on port 8089 with volume: {volume_name}...")

        # Build Locust's image
        build_command = [
            "docker",
            "build",
            "-f",
            os.path.join(docker_dir, "images/Dockerfile.locust"),
            "-t",
            "locust-image",
            ".",
        ]
        click.echo(f"Build command: {' '.join(build_command)}")
        subprocess.run(build_command, check=True)

        # Define the locustfile path
        locustfile_path = os.path.join(core_dir, "bootstraps/locustfile_bootstrap.py")
        if module:
            locustfile_path = f"{modules_dir}/{module}/tests/locustfile.py"

        # Run the Locust container
        up_command = [
            "docker",
            "run",
            "-d",
            "-p",
            "8089:8089",
            "-v",
            f"{volume_name}:/app",
            "--name",
            "locust_container",
            "--network",
            "docker_uvlhub_network",
            "locust-image",
            "-f",
            locustfile_path,
        ]

        click.echo(f"Docker Run command: {' '.join(up_command)}")
        subprocess.run(up_command, check=True)
        click.echo(click.style("Locust is running at http://localhost:8089", fg="green"))

    def is_locust_running():
        """Check if Locust is already running."""
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] == "locust":
                return True
        return False

    def run_in_console(module):

        if is_locust_running():
            click.echo("Locust is already running.")
            return

        locustfile_path = os.path.join(core_dir, "bootstraps/locustfile_bootstrap.py")
        if module:
            locustfile_path = os.path.join(modules_dir, module, "tests", "locustfile.py")
        locust_command = ["locust", "-f", locustfile_path]
        click.echo(f"Locust command: {' '.join(locust_command)}")
        subprocess.Popen(
            locust_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        click.echo(click.style("Locust is running at http://localhost:8089", fg="green"))

    def run_local_locust(module):
        """Run Locust in the local environment."""
        click.echo("Starting Locust in local environment on port 8089...")
        run_in_console(module)

    def run_vagrant_locust(module):
        """Run Locust in the Vagrant environment."""
        click.echo("Starting Locust in Vagrant environment on port 8089...")
        run_in_console(module)

    # Validate module if provided
    if module:
        validate_module(module)

    if working_dir == "/app/":
        client = docker.from_env()

        try:
            web_container = client.containers.get("web_app_container")
            volume_name = next(
                (
                    mount.get("Name") or mount.get("Source")
                    for mount in web_container.attrs["Mounts"]
                    if mount["Destination"] == "/app"
                ),
                None,
            )

            if not volume_name:
                raise ValueError("No volume or bind mount found mounted on /app")

            run_docker_locust(volume_name, module)

        except docker.errors.NotFound:
            click.echo(click.style("Web container not found.", fg="red"))
        except Exception as e:
            click.echo(click.style(f"An error occurred: {str(e)}", fg="red"))

    elif working_dir == "":
        run_local_locust(module)

    elif working_dir == "/vagrant/":
        run_vagrant_locust(module)

    else:
        click.echo(click.style(f"Unrecognized WORKING_DIR: {working_dir}", fg="red"))


@click.command("locust:stop", help="Stops the Locust container if it is running.")
def stop():
    working_dir = os.getenv("WORKING_DIR", "")

    def stop_local_locust():
        """Stop Locust process in the local environment."""
        click.echo("Stopping Locust in local environment...")
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] == "locust":
                click.echo(f"Stopping Locust process with PID {proc.info['pid']}...")
                os.kill(proc.info["pid"], signal.SIGTERM)

    def stop_docker_locust():
        click.echo("Stopping Locust container if it is running...")
        stop_command = ["docker", "stop", "locust_container"]
        rm_command = ["docker", "rm", "locust_container"]

        # Stop the Locust container if it is running
        subprocess.run(stop_command)

        # Remove the Locust container
        subprocess.run(rm_command)

    if working_dir == "/app/":
        stop_docker_locust()

    elif working_dir == "" or working_dir == "/vagrant/":
        stop_local_locust()

    else:
        click.echo(click.style(f"Unrecognized WORKING_DIR: {working_dir}", fg="red"))
