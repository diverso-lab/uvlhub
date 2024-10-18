import click
import os
import subprocess

# Define la ruta donde están los módulos
MODULES_DIR = os.path.join(os.getenv('WORKING_DIR', ''), 'app', 'modules')

# Lista de directorios que no queremos iterar
EXCLUDED_DIRS = {'.pytest_cache', '__pycache__'}


@click.command('webpack:compile', help="Iterate over each module's webpack.config.js and compile them.")
def webpack_compile():
    # Iterar sobre cada subdirectorio dentro de 'app/modules'
    for module in os.listdir(MODULES_DIR):
        module_path = os.path.join(MODULES_DIR, module)

        # Verificar si es un directorio y no está en la lista de excluidos
        if os.path.isdir(module_path) and module not in EXCLUDED_DIRS:
            webpack_file = os.path.join(module_path, 'assets', 'js', 'webpack.config.js')

            # Verificar si el archivo webpack.config.js existe en este módulo
            if os.path.exists(webpack_file):
                click.echo(f"Compiling {module}...")
                
                # Construir el comando de Webpack
                webpack_command = f'npx webpack --config {webpack_file} --mode development'
                
                # Ejecutar el comando
                try:
                    subprocess.run(webpack_command, shell=True, check=True)
                    click.echo(click.style(f"Successfully compiled {module}!", fg='green'))
                except subprocess.CalledProcessError as e:
                    click.echo(click.style(f"Error compiling {module}: {e}", fg='red'))
            else:
                click.echo(click.style(f"No webpack.config.js found in {module}, skipping...", fg='yellow'))
