import os
import stat

import click
from jinja2 import Environment, FileSystemLoader, select_autoescape


def pascalcase(s):
    """Converts string to PascalCase."""
    return "".join(word.capitalize() for word in s.split("_"))


def setup_jinja_env():
    """Configures and returns a Jinja environment."""
    env = Environment(
        loader=FileSystemLoader(searchpath="./rosemary/templates"),
        autoescape=select_autoescape(["html", "xml", "j2"]),
    )
    env.filters["pascalcase"] = pascalcase
    return env


def render_and_write_file(env, template_name, filename, context):
    """Renders a template and writes it to a specified file."""
    template = env.get_template(template_name)
    content = template.render(context) + "\n"
    with open(filename, "w") as f:
        f.write(content)


@click.command("make:module", help="Creates a new module with a given name.")
@click.argument("name")
def make_module(name):
    modules_root_path = os.path.join(os.getenv("WORKING_DIR", ""), "app/modules")
    module_path = f"{modules_root_path}/{name}"

    if os.path.exists(module_path):
        click.echo(click.style(f"The module '{name}' already exists.", fg="red"))
        return

    env = setup_jinja_env()

    # Defines the directories to create.
    directories = {"templates"}

    files_and_templates = {
        "__init__.py": "module_init.py.j2",
        "routes.py": "module_routes.py.j2",
        "models.py": "module_models.py.j2",
        "repositories.py": "module_repositories.py.j2",
        "services.py": "module_services.py.j2",
        "forms.py": "module_forms.py.j2",
        "seeders.py": "module_seeders.py.j2",
        os.path.join("templates", name, "index.html"): "module_templates_index.html.j2",
        "assets/js/scripts.js": "module_scripts.js.j2",
        "assets/js/webpack.config.js": "module_webpack.config.js.j2",
        "tests/test_unit.py": "module_tests_test_unit.py.j2",
        "tests/locustfile.py": "module_tests_locustfile.py.j2",
        "tests/test_selenium.py": "module_tests_test_selenium.py.j2",
    }

    # Create the necessary directories, explicitly excluding 'tests' from the creation of subfolders.
    for directory in directories:
        os.makedirs(os.path.join(module_path, directory, name), exist_ok=True)

    # Create 'tests' directory directly under module_path, without additional subfolders.
    os.makedirs(os.path.join(module_path, "tests"), exist_ok=True)

    # Create 'assets' directory directly under module_path
    os.makedirs(os.path.join(module_path, "assets", "css"), exist_ok=True)
    os.makedirs(os.path.join(module_path, "assets", "js"), exist_ok=True)

    # Create empty __init__.py file directly in the 'tests' directory.
    open(os.path.join(module_path, "tests", "__init__.py"), "a").close()

    # Render and write files, including 'test_unit.py' directly in 'tests'.
    for filename, template_name in files_and_templates.items():
        if template_name:  # Check if there is a defined template.
            render_and_write_file(
                env,
                template_name,
                os.path.join(module_path, filename),
                {"module_name": name},
            )
        else:
            open(os.path.join(module_path, filename), "a").close()  # Create empty file if there is no template.

    click.echo(click.style(f"Module '{name}' created successfully.", fg="green"))

    # Change the owner of the main folder of the module
    os.chown(module_path, 1000, 1000)

    # Change permissions to drwxrwxr-x (chmod 775)
    os.chmod(module_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    # Change the owner of all created files and directories to UID 1000 and GID 1000
    uid = 1000
    gid = 1000

    for root, dirs, files in os.walk(module_path):
        for dir_ in dirs:
            dir_path = os.path.join(root, dir_)
            os.chown(dir_path, uid, gid)
            os.chmod(dir_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

        for file_ in files:
            file_path = os.path.join(root, file_)
            os.chown(file_path, uid, gid)
            os.chmod(
                file_path,
                stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH,
            )

    click.echo(click.style(f"Module '{name}' permissions changed successfully.", fg="green"))
