from flask import abort, request

from app.features.webhook import webhook_bp
from app.features.webhook.services import WebhookService

webhook_service = WebhookService()


@webhook_bp.route("/webhook/deploy", methods=["POST"])
def deploy():
    if not webhook_service.is_authorized(request.headers.get("Authorization")):
        abort(403, description="Unauthorized")

    webhook_service.deploy()
    return "Deployment successful", 200
