import os
import subprocess
import click
import core.selenium.common as driver_selector
import docker



@click.command("selenium", help="Executes Selenium tests based on the environment.")
@click.argument("module", required=False)
@click.option("--driver", default="firefox", type=click.Choice(["firefox", "chrome"], case_sensitive=False), help="Specify the Selenium WebDriver to use.")
@click.option("--video", default="false", type=click.Choice(["true", "false"], case_sensitive=False), help="Specify if you would like to record the tests.")
def selenium(module, driver, video):
    try:
        # Absolute paths
        working_dir = os.getenv("WORKING_DIR", "")
        modules_dir = os.path.join(working_dir, "app/modules")
        driver_selector.set_service_driver(driver)

        def validate_module(module):
            """Check if the module exists and if the selenium test file exists."""
            if module:
                module_path = os.path.join(modules_dir, module)
                if not os.path.exists(module_path):
                    raise click.UsageError(f"Module '{module}' does not exist.")
                selenium_test_path = os.path.join(module_path, "tests", "test_selenium.py")
                if not os.path.exists(selenium_test_path):
                    raise click.UsageError(
                        f"Selenium test for module '{module}' does not exist at path "
                        f"'{selenium_test_path}'."
                    )

        def run_selenium_tests_in_local(module):
            """Run the Selenium tests in the local environment."""
            if module:
                selenium_test_path = os.path.join(modules_dir, module, "tests", "test_selenium.py")
                test_command = ["python", selenium_test_path]
            else:
                selenium_test_paths = []
                for module in os.listdir(modules_dir):
                    tests_dir = os.path.join(modules_dir, module, "tests")
                    selenium_test_path = os.path.join(tests_dir, "test_selenium.py")
                    if os.path.exists(selenium_test_path):
                        selenium_test_paths.append(selenium_test_path)
                test_command = ["python"] + selenium_test_paths

            click.echo(f"Running Selenium tests with command: {' '.join(test_command)}")
            subprocess.run(test_command, check=True)

        def run_docker_selenium_tests(module):
            client = docker.from_env()
            """Run the Selenium tests in a Docker container."""
            if module:
                selenium_test_path = os.path.join(modules_dir, module, "tests", "test_selenium.py")
                test_command = ["pytest", selenium_test_path]
            else:
                selenium_test_paths = []
                for module in os.listdir(modules_dir):
                    tests_dir = os.path.join(modules_dir, module, "tests")
                    selenium_test_path = os.path.join(tests_dir, "test_selenium.py")
                    if os.path.exists(selenium_test_path):
                        selenium_test_paths.append(selenium_test_path)
                test_command = ["pytest"] + selenium_test_paths
            docker_dir = os.path.join(working_dir, "docker/")
            docker_compose_file = os.path.join(docker_dir, "docker-compose-video.yml")
            service_name = "firefox_video"
            try:
                # Check if the container already exists
                if os.environ.get("SERVICE_DRIVER", "firefox") == 'firefox':
                    client.containers.get("firefox-video")
                    click.echo("firefox-video container is already running.")
                elif os.environ.get("SERVICE_DRIVER", "firefox") == 'chrome':
                    client.containers.get("chrome-video")
                    click.echo("chrome-video container is already running.")
                else:
                    click.echo(click.style("Driver not supported, choosing firefox.", fg='red'))
            except docker.errors.NotFound:
                # Container does not exist, proceed to create it (happy path)
                if os.environ.get("SERVICE_DRIVER", "firefox") == 'chrome':
                    service_name = "chrome_video"
                click.echo("Creating firefox-video container. Please be patient this make take a bit")
                subprocess.run(f"docker compose -f {docker_compose_file} up -d {service_name}", check=True, shell=True)
                pass

            click.echo("Selenium-grid is running at http://localhost:4444")
            click.echo(
                click.style("Remember test are collected first, and then runned, please be patient",
                            fg="yellow")
            )
            click.echo(
                click.style("Please check your sessions in http://localhost:4444/ui/#/sessions after test collection is finished", fg="green")
            )
            click.echo(f"Running Selenium tests with command: {' '.join(test_command)}")
            subprocess.run(test_command, check=True)
            # we remove firefox and chrome video containers in order to access videos
            subprocess.run(f"docker compose -f {docker_compose_file} down", check=True, shell=True)
            click.echo(click.style("All test have been executed.", fg="green"))

        def record_selenium_tests(module):
            client = docker.from_env()
            """Records Selenium tests for both firefox and chrome drivers."""
            if module:
                selenium_test_path = os.path.join(modules_dir, module, "tests", "test_selenium.py")
                test_command = ["pytest", selenium_test_path]
            else:
                selenium_test_paths = []
                for module in os.listdir(modules_dir):
                    tests_dir = os.path.join(modules_dir, module, "tests")
                    selenium_test_path = os.path.join(tests_dir, "test_selenium.py")
                    if os.path.exists(selenium_test_path):
                        selenium_test_paths.append(selenium_test_path)
                test_command = ["pytest"] + selenium_test_paths
            docker_dir = os.path.join(working_dir, "docker/")
            docker_compose_file = os.path.join(docker_dir, "docker-compose-video.yml")
            try:
                # Check if containers already exist
                client.containers.get("firefox-video")
                click.echo("firefox-video container is already running.")
                client.containers.get("chrome-video")
                click.echo("chrome-video container is already running.")
            except docker.errors.NotFound:
                click.echo(click.style("Something went wrong. Containers don't exist", fg="red"))
                click.echo(click.style("Try running 'docker compose -f docker/docker-compose-video.yml up -d' ON YOUR HOST, NOT YOUR CONTAINER before using this command", fg="red"))
                return
            click.echo("Selenium-grid is running at http://localhost:4444")
            click.echo(
                click.style("Remember test are collected first, and then runned, please be patient",
                            fg="yellow")
            )
            click.echo(
                click.style("Please check your sessions in http://localhost:4444/ui/#/sessions after test collection is finished", fg="green")
            )
            click.echo(f"Running Selenium tests with command: {' '.join(test_command)}")
            subprocess.run(test_command, check=True)
            # we remove firefox and chrome video containers in order to access videos
            subprocess.run(f"docker compose -f {docker_compose_file} down", check=True, shell=True)
            click.echo(
                click.style("All test have been executed. Please check /docker/tmp/videos for watching full test executions",
                            fg="green")
            )
            click.echo(click.style("If videos don't appear try running '/scripts/clean_docker.sh'. \
            Then, run your docker-compose.dev and before running rosemary selenium don't forget to \
            run this command: 'docker compose -f docker/docker-compose-video.yml up -d'", fg="blue"))

        def run_vagrant_selenium_tests(module):
            """Run the Selenium tests in a Vagrant environment."""
            click.echo(
                click.style(
                    "Currently it is not possible to run Selenium tests from a Vagrant environment. "
                    "Do you want to implement it yourself? ^^",
                    fg="red",
                )
            )

        # Validate module if provided
        if module:
            validate_module(module)

        # Check the environment and decide how to run the tests
        if working_dir == "/app/":
            if video == "true":
                record_selenium_tests(module)
            else:
                run_docker_selenium_tests(module)

        elif working_dir == "":
            run_selenium_tests_in_local(module)

        elif working_dir == "/vagrant/":
            run_vagrant_selenium_tests(module)

        else:
            click.echo(click.style(f"Unrecognized WORKING_DIR: {working_dir}", fg="red"))

    finally:
        driver_selector.set_service_driver("firefox")
