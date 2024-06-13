import click
import os
import subprocess


@click.command()
def update():
    """This command updates all packages based on the requirements.txt, excluding editable installations, and updates
    the file with concrete versions."""
    requirements_path = os.path.join(os.getenv('WORKING_DIR', ''), 'requirements.txt')
    try:
        # Update pip first
        subprocess.check_call(['pip', 'install', '--upgrade', 'pip'])

        # Read current requirements, excluding -e packages
        with open(requirements_path, 'r') as f:
            requirements = [line.strip() for line in f if not line.startswith("-e")]

        # Update each package
        for requirement in requirements:
            package_name = requirement.split('==')[0]
            if package_name:  # Ensure it's not an empty package name
                subprocess.check_call(['pip', 'install', '--upgrade', package_name])

        # Generate a new requirements.txt, excluding editable installations
        freeze_output = subprocess.check_output(['pip', 'freeze']).decode('utf-8')
        with open(requirements_path, 'w') as f:
            for line in freeze_output.split('\n'):
                if not line.startswith("-e"):
                    f.write(line + '\n')

        click.echo(click.style('Update completed!', fg='green'))
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f'Error during the update: {e}', fg='red'))


if __name__ == '__main__':
    update()
