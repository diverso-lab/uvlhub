import hmac
import os
import subprocess
from datetime import datetime

import pytz
from flask import abort

import docker

client = docker.from_env()

# Commands run inside every target container, in order, on each deploy.
DEPLOY_COMMANDS = (
    "/workspace/scripts/git_update.sh",  # pull the latest code
    "pip install --pre .",  # update dependencies pinned in pyproject.toml
    "pip install -e ./rosemary",  # update the Rosemary CLI
)


class WebhookService:
    """Drives container redeploys triggered by an authenticated webhook. Owns no
    domain entity, so it is a plain service."""

    def is_authorized(self, auth_header: str | None) -> bool:
        token = os.getenv("WEBHOOK_TOKEN")
        if not token or not auth_header:
            return False
        # Constant-time comparison to avoid leaking the token via timing.
        return hmac.compare_digest(auth_header, f"Bearer {token}")

    def get_web_container(self):
        try:
            return client.containers.get("web_app_container")
        except docker.errors.NotFound:
            abort(404, description="Web container not found.")

    def get_worker_container(self):
        try:
            return client.containers.get("rq_worker_container")
        except docker.errors.NotFound:
            abort(404, description="Worker container not found.")

    def get_volume_name(self, container):
        volume_name = next(
            (
                mount.get("Name") or mount.get("Source")
                for mount in container.attrs["Mounts"]
                if mount["Destination"] == "/workspace"
            ),
            None,
        )

        if not volume_name:
            raise ValueError("No volume or bind mount found mounted on /workspace")

        return volume_name

    def execute_host_command(self, volume_name, command):
        try:
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{volume_name}:/workspace",
                    "-v",
                    "/var/run/docker.sock:/var/run/docker.sock",
                    "-w",
                    "/workspace",
                    *command,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            abort(500, description=f"Host command failed: {str(e)}")

    def execute_container_command(self, container, command, workdir="/workspace"):
        exit_code, output = container.exec_run(command, workdir=workdir)
        if exit_code != 0:
            abort(500, description=f"Container command failed: {output.decode('utf-8')}")
        return output.decode("utf-8")

    def log_deployment(self, container):
        log_entry = f"Deployment successful at {datetime.now(pytz.utc)}\n"
        log_file_path = "/workspace/deployments.log"
        self.execute_container_command(container, f"sh -c 'echo \"{log_entry}\" >> {log_file_path}'")

    def restart_container(self, container):
        subprocess.Popen(["/bin/sh", "/workspace/scripts/restart_container.sh", container.id])

    def deploy(self):
        """Update and restart the worker and web containers."""
        for container in (self.get_worker_container(), self.get_web_container()):
            for command in DEPLOY_COMMANDS:
                self.execute_container_command(container, command)
            self.log_deployment(container)
            self.restart_container(container)
