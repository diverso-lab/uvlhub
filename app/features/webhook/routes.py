import os

from dotenv import load_dotenv
from flask import abort, request

from app.features.webhook import webhook_bp
from app.features.webhook.services import WebhookService

load_dotenv()

WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN")


@webhook_bp.route("/webhook/deploy", methods=["POST"])
def deploy():

    token = request.headers.get("Authorization")
    if token != f"Bearer {WEBHOOK_TOKEN}":
        abort(403, description="Unauthorized")

    service = WebhookService()

    containers = [
        service.get_worker_container(),
        service.get_web_container(),
    ]

    for container in containers:
        # Pull the latest code
        service.execute_container_command(container, "/workspace/scripts/git_update.sh")

        # Update dependencies (pinned in pyproject.toml)
        service.execute_container_command(container, "pip install --pre .")

        # Update Rosemary CLI
        service.execute_container_command(container, "pip install -e ./rosemary")

        # Deployment log
        service.log_deployment(container)

        # Container restart
        service.restart_container(container)

    return "Deployment successful", 200
