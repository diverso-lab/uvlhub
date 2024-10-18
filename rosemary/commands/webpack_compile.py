import click
import os
import subprocess

# Define the path where the modules are located
MODULES_DIR = os.path.join(os.getenv('WORKING_DIR', ''), 'app', 'modules')

# List of directories to exclude from iteration
EXCLUDED_DIRS = {'.pytest_cache', '__pycache__'}


@click.command('webpack:compile', help="Compile webpack for one or all modules.")
@click.argument('module_name', required=False)
def webpack_compile(module_name):
    # Check if a specific module name was provided
    if module_name:

        # Verify if the module exists
        module_path = os.path.join(MODULES_DIR, module_name)
        if not os.path.exists(module_path) or not os.path.isdir(module_path):
            click.echo(click.style(f"Module '{module_name}' does not exist.", fg='red'))
            return

        # Compile only the specified module
        compile_module(module_name)
    else:
        # Iterate over each subdirectory in 'app/modules'
        for module in os.listdir(MODULES_DIR):
            module_path = os.path.join(MODULES_DIR, module)

            # Check if it's a directory and not in the excluded list
            if os.path.isdir(module_path) and module not in EXCLUDED_DIRS:
                compile_module(module)


def compile_module(module):
    module_path = os.path.join(MODULES_DIR, module)
    webpack_file = os.path.join(module_path, 'assets', 'js', 'webpack.config.js')

    # Check if the webpack.config.js file exists for this module
    if os.path.exists(webpack_file):
        click.echo(f"Compiling {module}...")

        # Build the Webpack command
        webpack_command = f'npx webpack --config {webpack_file} --mode development'

        # Run the command
        try:
            subprocess.run(webpack_command, shell=True, check=True)
            click.echo(click.style(f"Successfully compiled {module}!", fg='green'))
        except subprocess.CalledProcessError as e:
            click.echo(click.style(f"Error compiling {module}: {e}", fg='red'))
    else:
        click.echo(click.style(f"No webpack.config.js found in {module}, skipping...", fg='yellow'))
