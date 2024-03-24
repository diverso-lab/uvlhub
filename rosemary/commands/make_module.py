import click
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os


def pascalcase(s):
    """Converts string to PascalCase."""
    return ''.join(word.capitalize() for word in s.split('_'))


def setup_jinja_env():
    """Configures and returns a Jinja environment."""
    env = Environment(
        loader=FileSystemLoader(searchpath="./rosemary/templates"),
        autoescape=select_autoescape(['html', 'xml', 'j2'])
    )
    env.filters['pascalcase'] = pascalcase
    return env


def render_and_write_file(env, template_name, filename, context):
    """Renders a template and writes it to a specified file."""
    template = env.get_template(template_name)
    content = template.render(context) + "\n"
    with open(filename, 'w') as f:
        f.write(content)


@click.command('make:module', help="Creates a new module with a given name.")
@click.argument('name')
def make_module(name):
    blueprint_path = f'app/blueprints/{name}'

    if os.path.exists(blueprint_path):
        click.echo(f"The module '{name}' already exists.")
        return

    env = setup_jinja_env()

    files_and_templates = {
        '__init__.py': 'blueprint_init.py.j2',
        'routes.py': 'blueprint_routes.py.j2',
        'models.py': 'blueprint_models.py.j2',
        'repositories.py': 'blueprint_repositories.py.j2',
        'services.py': 'blueprint_services.py.j2',
        'forms.py': 'blueprint_forms.py.j2',
        os.path.join('templates', name, 'index.html'): 'blueprint_templates_index.html.j2'
    }

    # Create necessary directories
    os.makedirs(os.path.join(blueprint_path, 'templates', name), exist_ok=True)

    # Render and write files
    for filename, template_name in files_and_templates.items():
        render_and_write_file(env, template_name, os.path.join(blueprint_path, filename), {'blueprint_name': name})

    click.echo(f"Module '{name}' created successfully.")
