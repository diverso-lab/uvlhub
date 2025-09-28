import logging
import os
import subprocess

import click

logger = logging.getLogger(__name__)

# Define the path where the modules are located
MODULES_DIR = os.path.join(os.getenv("WORKING_DIR", ""), "app", "modules")


# Function to load excluded directories from .moduleignore
def load_excluded_modules():
    # Start with a list of directories that should always be excluded
    excluded_modules = [".pytest_cache", "__pycache__"]
    moduleignore_path = os.path.join(os.getenv("WORKING_DIR", ""), ".moduleignore")

    # Check if .moduleignore exists and load its content
    if os.path.exists(moduleignore_path):
        with open(moduleignore_path, "r") as f:
            # Add each non-empty line from .moduleignore to the excluded_modules list
            excluded_modules.extend([line.strip() for line in f if line.strip()])

    return excluded_modules


EXCLUDED_MODULES = load_excluded_modules()


@click.command("webpack:compile", help="Compile webpack for one or all modules.")
@click.argument("module_name", required=False)
@click.option("--watch", is_flag=True, help="Enable watch mode for development.")
def webpack_compile(module_name, watch):
    # Detect if we are in production or development mode according to FLASK_ENV
    flask_env = os.getenv("FLASK_ENV", "develop")  # Default to 'develop' if not defined
    production = flask_env == "production"  # True if we are in production

    # Check if a specific module was provided
    if module_name:
        module_path = os.path.join(MODULES_DIR, module_name)
        if not os.path.exists(module_path) or not os.path.isdir(module_path):
            click.echo(click.style(f"Module '{module_name}' does not exist.", fg="red"))
            return
        compile_module(module_name, watch, production)
    else:
        for module in os.listdir(MODULES_DIR):
            module_path = os.path.join(MODULES_DIR, module)
            if os.path.isdir(module_path) and module not in EXCLUDED_MODULES:
                compile_module(module, watch, production)


def compile_module(module, watch, production):
    module_path = os.path.join(MODULES_DIR, module)
    webpack_file = os.path.join(module_path, "assets", "js", "webpack.config.js")

    # Verify if the webpack.config.js file exists for this module
    if os.path.exists(webpack_file):
        click.echo(f"Compiling {module}...")

        # Determine mode based on FLASK_ENV
        mode = "production" if production else "development"

        # Add --watch flag only if we are in development mode
        watch_flag = "--watch" if watch and not production else ""

        # Define additional options depending on the environment (source maps and minimization)
        if production:
            # In production, minimization is enabled by default in Webpack production mode
            extra_flags = ""
        else:
            # In development, enable source maps
            extra_flags = "--devtool source-map --no-cache"

        # Add --color flag to force colored output
        webpack_command = f"npx webpack --config {webpack_file} --mode {mode} {watch_flag} {extra_flags} --color"

        # Use Popen to execute the command without blocking the console
        try:
            if watch:
                # Execute in the background without blocking the console, redirecting only stderr to os.devnull
                subprocess.Popen(webpack_command, shell=True, stdout=None, stderr=subprocess.DEVNULL)
                click.echo(click.style(f"Started watching {module} in {mode} mode!", fg="blue"))

            else:
                # Blocking execution for normal compilation without watch
                subprocess.run(webpack_command, shell=True, check=True)
                click.echo(click.style(f"Successfully compiled {module} in {mode} mode!", fg="green"))

        except subprocess.CalledProcessError as e:
            click.echo(click.style(f"Error compiling {module}: {e}", fg="red"))
            raise
    else:
        click.echo(click.style(f"No webpack.config.js found in {module}, skipping...", fg="yellow"))
