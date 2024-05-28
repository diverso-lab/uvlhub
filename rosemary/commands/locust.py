import os
import subprocess
import click

@click.command('locust', help="Launches Locust for load testing based on the environment.")
def locust():
    working_dir = os.getenv('WORKING_DIR', '/app')  # Asegúrate de que WORKING_DIR tenga un valor por defecto
    compose_file_path = os.path.join(working_dir, 'docker', 'docker-compose.dev.yml')

    if working_dir in ['/app', '/app/']:
        click.echo("Starting Locust service using Docker Compose...")

        # Construir la imagen de Locust
        build_command = ['docker-compose', '-f', compose_file_path, 'build']
        click.echo(f"Build command: {' '.join(build_command)}")
        subprocess.run(build_command)

        # Iniciar el servicio de Locust usando Docker Compose con el perfil 'locust'
        up_command = ['docker-compose', '-f', compose_file_path, 'up', '-d', '--profile', 'locust']
        click.echo(f"Docker Compose command: {' '.join(up_command)}")
        subprocess.run(up_command)
    elif working_dir == '':
        click.echo("Starting Locust in local environment on port 8990...")
        subprocess.run(['locust', '-f', 'locustfile.py', '--headless', '-u', '10', '-r', '1', '--host=http://localhost:8990'])
    elif working_dir == '/vagrant/':
        click.echo("Starting Locust in Vagrant environment on port 8990...")
        subprocess.run(['vagrant', 'ssh', '--command', f'locust -f /vagrant/app/locustfile.py --headless -u 10 -r 1 --host=http://localhost:8990'])
    else:
        click.echo(click.style(f"Unrecognized WORKING_DIR: {working_dir}", fg='red'))
