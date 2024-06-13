import os
import subprocess
import click


@click.command('selenium', help="Executes Selenium tests based on the environment.")
@click.argument('blueprint', required=False)
def selenium(blueprint):
    # Absolute paths
    working_dir = os.getenv('WORKING_DIR', '')
    blueprints_dir = os.path.join(working_dir, 'app/blueprints')

    def validate_blueprint(blueprint):
        """Check if the blueprint exists."""
        if blueprint:
            blueprint_path = os.path.join(blueprints_dir, blueprint)
            if not os.path.exists(blueprint_path):
                raise click.UsageError(f"Blueprint '{blueprint}' does not exist.")
            selenium_test_path = os.path.join(blueprint_path, 'tests', 'test_selenium.py')
            if not os.path.exists(selenium_test_path):
                raise click.UsageError(
                    f"Selenium test for blueprint '{blueprint}' does not exist at path "
                    f"'{selenium_test_path}'."
                )

    def run_selenium_tests_in_local(blueprint):
        """Run the Selenium tests."""
        if blueprint:
            selenium_test_path = os.path.join(blueprints_dir, blueprint, 'tests', 'test_selenium.py')
            test_command = ['python', selenium_test_path]
        else:
            selenium_test_paths = []
            for module in os.listdir(blueprints_dir):
                tests_dir = os.path.join(blueprints_dir, module, 'tests')
                selenium_test_path = os.path.join(tests_dir, 'test_selenium.py')
                if os.path.exists(selenium_test_path):
                    selenium_test_paths.append(selenium_test_path)
            test_command = ['python'] + selenium_test_paths

        click.echo(f"Running Selenium tests with command: {' '.join(test_command)}")
        subprocess.run(test_command, check=True)

    # Validate blueprint if provided
    if blueprint:
        validate_blueprint(blueprint)

    if working_dir == '/app/':

        click.echo(click.style(
            "Currently it is not possible to run this "
            "command from a Docker environment, do you want to implement it yourself? ^^",
            fg='red'
        ))

    elif working_dir == '':
        run_selenium_tests_in_local(blueprint)

    elif working_dir == '/vagrant/':

        click.echo(click.style(
            "Currently it is not possible to run this "
            "command from a Vagrant environment, do you want to implement it yourself? ^^",
            fg='red'
        ))

    else:
        click.echo(click.style(f"Unrecognized WORKING_DIR: {working_dir}", fg='red'))
