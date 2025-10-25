import os
import subprocess

import click

import core.selenium.common as driver_selector


@click.command("selenium", help="Executes Selenium tests based on the environment (local, Docker, or Vagrant).")
@click.argument("module", required=False)
@click.option(
    "--driver",
    default="firefox",
    type=click.Choice(["firefox", "chrome"], case_sensitive=False),
    help="Specify the Selenium WebDriver to use.",
)
def selenium(module, driver):
    """Unified Selenium test runner for local, Docker, and Vagrant environments."""
    try:
        # =====================
        # Environment detection
        # =====================
        working_dir = os.getenv("WORKING_DIR", "")
        modules_dir = os.path.join(working_dir, "app/modules")
        driver_selector.set_service_driver(driver)

        # =====================
        # Helper functions
        # =====================

        def validate_module(module_name):
            """Check if the module exists and has a Selenium test."""
            if not module_name:
                return
            module_path = os.path.join(modules_dir, module_name)
            if not os.path.exists(module_path):
                raise click.UsageError(f"Module '{module_name}' does not exist.")
            selenium_test_path = os.path.join(module_path, "tests", "test_selenium.py")
            if not os.path.exists(selenium_test_path):
                raise click.UsageError(f"Selenium test for module '{module_name}' not found at '{selenium_test_path}'.")

        def collect_test_paths(module_name=None):
            """Collect Selenium test files for one or all modules."""
            if module_name:
                return [os.path.join(modules_dir, module_name, "tests", "test_selenium.py")]
            paths = []
            for m in os.listdir(modules_dir):
                selenium_test = os.path.join(modules_dir, m, "tests", "test_selenium.py")
                if os.path.exists(selenium_test):
                    paths.append(selenium_test)
            return paths

        def run_selenium_tests(module_name, env="local"):
            """Run Selenium tests in the specified environment."""
            test_paths = collect_test_paths(module_name)
            base_cmd = "pytest" if env == "docker" else "python"
            cmd = [base_cmd] + test_paths

            env_label = "Docker (Selenium Grid)" if env == "docker" else "local environment"
            click.echo(click.style(f"🚀 Running Selenium tests in {env_label}...", fg="cyan"))
            click.echo(f"→ Command: {' '.join(cmd)}")

            try:
                subprocess.run(cmd, check=True)
                click.echo(click.style("✅ Selenium tests completed successfully.", fg="green"))
            except subprocess.CalledProcessError:
                click.echo(click.style("❌ Selenium tests failed.", fg="red"))
                raise

        def run_vagrant_tests(module_name):
            """Placeholder for future Vagrant integration."""
            click.echo(
                click.style(
                    "Currently it is not possible to run Selenium tests from a Vagrant environment. "
                    "Do you want to implement it yourself? https://github.com/diverso-lab/uvlhub/pulls",
                    fg="red",
                )
            )

        # =====================
        # Main flow
        # =====================
        if module:
            validate_module(module)

        if working_dir == "/app/":
            run_selenium_tests(module, env="docker")
        elif working_dir == "":
            run_selenium_tests(module, env="local")
        elif working_dir == "/vagrant/":
            run_vagrant_tests(module)
        else:
            click.echo(click.style(f"Unrecognized WORKING_DIR: {working_dir}", fg="red"))

    except click.UsageError as e:
        raise e
    except subprocess.CalledProcessError:
        # subprocess already echoed a failure message
        pass
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {e}", fg="red"))
    finally:
        # Reset driver to default after execution
        driver_selector.set_service_driver("firefox")
