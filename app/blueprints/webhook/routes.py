from flask import request, abort
import os
from dotenv import load_dotenv
from app.blueprints.webhook import webhook_bp
from app.blueprints.webhook.services import WebhookService
load_dotenv()

WEBHOOK_TOKEN = os.getenv('WEBHOOK_TOKEN')


@webhook_bp.route('/webhook/deploy', methods=['GET'])
def deploy():

    token = request.headers.get('Authorization')
    if token != f"Bearer {WEBHOOK_TOKEN}":
        abort(403, description="Unauthorized")

    service = WebhookService()

    web_container = service.get_web_container()
    volume_name = service.get_volume_name(web_container)

    # Pull the latest code on the host
    service.execute_host_command(volume_name, ['alpine/git', 'pull'])

    # Update dependencies in the container
    service.execute_container_command(web_container, 'pip install -r requirements.txt')

    # Run migrations in the container
    service.execute_container_command(web_container, 'flask db upgrade')

    # Log the deployment
    service.log_deployment(web_container)

    return 'Deployment successful', 200
