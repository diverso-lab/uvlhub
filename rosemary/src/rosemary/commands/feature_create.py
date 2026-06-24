import os
import stat

import click
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Templates ship inside the rosemary package (src layout), resolved relative to
# this file so the command works regardless of the current working directory.
_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")


def pascalcase(s):
    """Converts string to PascalCase."""
    return "".join(word.capitalize() for word in s.split("_"))


def setup_jinja_env():
    """Configures and returns a Jinja environment."""
    env = Environment(
        loader=FileSystemLoader(searchpath=_TEMPLATES_DIR),
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


@click.command("feature:create", help="Creates a new feature with a given name.")
@click.argument("name")
def feature_create(name):
    features_root_path = os.path.join(os.getenv("WORKING_DIR", ""), "app/features")
    feature_path = f"{features_root_path}/{name}"

    if os.path.exists(feature_path):
        click.echo(click.style(f"The feature '{name}' already exists.", fg="red"))
        return

    env = setup_jinja_env()

    files_and_templates = {
        "__init__.py": "feature_init.py.j2",
        "routes.py": "feature_routes.py.j2",
        "models.py": "feature_models.py.j2",
        "repositories.py": "feature_repositories.py.j2",
        "services.py": "feature_services.py.j2",
        "forms.py": "feature_forms.py.j2",
        "seeders.py": "feature_seeders.py.j2",
        os.path.join("templates", name, "index.html"): "feature_templates_index.html.j2",
        "assets/js/scripts.js": "feature_scripts.js.j2",
        "assets/js/webpack.config.js": "feature_webpack.config.js.j2",
        # Testing pyramid (one file per level, each tagged with its pytest marker)
        "tests/test_unit.py": "feature_tests_test_unit.py.j2",
        "tests/test_repository.py": "feature_tests_test_repository.py.j2",
        "tests/test_service.py": "feature_tests_test_service.py.j2",
        "tests/test_integration.py": "feature_tests_test_integration.py.j2",
        "tests/test_selenium.py": "feature_tests_test_selenium.py.j2",
        "tests/locustfile.py": "feature_tests_locustfile.py.j2",
    }

    # Create directories
    os.makedirs(os.path.join(feature_path, "templates", name), exist_ok=True)
    os.makedirs(os.path.join(feature_path, "tests"), exist_ok=True)
    os.makedirs(os.path.join(feature_path, "assets", "css"), exist_ok=True)
    os.makedirs(os.path.join(feature_path, "assets", "js"), exist_ok=True)

    # Empty __init__.py for the tests package
    open(os.path.join(feature_path, "tests", "__init__.py"), "a").close()

    context = {"feature_name": name}
    for filename, template_name in files_and_templates.items():
        render_and_write_file(env, template_name, os.path.join(feature_path, filename), context)

    click.echo(click.style(f"Feature '{name}' created successfully.", fg="green"))

    # Match host UID/GID so files created from inside the dev container are owned
    # by the developer on the host (typical Docker dev workflow).
    uid, gid = 1000, 1000
    os.chown(feature_path, uid, gid)
    os.chmod(feature_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    for root, dirs, files in os.walk(feature_path):
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

    click.echo(click.style(f"Feature '{name}' permissions changed successfully.", fg="green"))
