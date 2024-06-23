from flask import Flask
import os
import subprocess
import docker
from dotenv import load_dotenv
from app.blueprints.webhook import webhook_bp

load_dotenv()

app = Flask(__name__)
WEBHOOK_TOKEN = os.getenv('WEBHOOK_TOKEN')

client = docker.from_env()


@webhook_bp.route('/webhook/deploy', methods=['GET'])
def deploy():
    '''
    token = request.headers.get('Authorization')
    if token != f"Bearer {WEBHOOK_TOKEN}":
        abort(403)
    '''

    try:
        web_container = client.containers.get('web_app_container')
        volume_name = next(
            (mount.get('Name') or mount.get('Source') for mount in web_container.attrs['Mounts']
                if mount['Destination'] == '/app'), None
        )

        if not volume_name:
            raise ValueError("No volume or bind mount found mounted on /app")

    except docker.errors.NotFound:
        return "Web container not found.", 404
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

    try:
        # Pull the latest code (in host)
        subprocess.run([
            'docker', 'run', '--rm',
            '-v', f'{volume_name}:/app',
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
            '-w', '/app',
            'alpine/git', 'pull'
        ], check=True)

        # Update dependencies
        web_container.exec_run('pip install -r requirements.txt', workdir='/app')

        # Run migrations
        web_container.exec_run('flask db upgrade', workdir='/app')

        return 'Deployment successful', 200
    except subprocess.CalledProcessError as e:
        return f"Deployment failed: {str(e)}", 500
