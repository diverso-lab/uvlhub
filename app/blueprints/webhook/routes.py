from flask import request, abort
import os
from dotenv import load_dotenv
from app.blueprints.webhook import webhook_bp
from app.blueprints.webhook.services import WebhookService
load_dotenv()

WEBHOOK_TOKEN = os.getenv('WEBHOOK_TOKEN')


@webhook_bp.route('/webhook/deploy', methods=['GET'])
def deploy():

    '''
    token = request.headers.get('Authorization')
    if token != f"Bearer {WEBHOOK_TOKEN}":
        abort(403, description="Unauthorized")
    '''

    service = WebhookService()

    web_container = service.get_web_container()

    # Pull the latest code in the container
    service.execute_container_command(web_container, 'git remote -v')
    service.execute_container_command(web_container, 'git remote set-url origin https://github.com/diverso-lab/uvlhub')
    service.execute_container_command(web_container, 'git pull origin main')

    # Update dependencies in the container
    service.execute_container_command(web_container, 'pip install -r requirements.txt')

    # Run migrations in the container
    service.execute_container_command(web_container, 'flask db upgrade')

    # Log the deployment
    service.log_deployment(web_container)

    return 'Deployment successful', 200
