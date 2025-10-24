import os

from dotenv import load_dotenv
from flask import abort, request

from app.modules.webhook import webhook_bp
from app.modules.webhook.services import WebhookService

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
        service.execute_container_command(container, "/app/scripts/git_update.sh")

        # Update dependencies
        service.execute_container_command(container, "pip install --pre -r requirements.txt")

        # Update Rosemary CLI
        service.execute_container_command(container, "pip install -e ./")

        # Deployment log
        service.log_deployment(container)

        # Container restart
        service.restart_container(container)

    return "Deployment successful", 200
