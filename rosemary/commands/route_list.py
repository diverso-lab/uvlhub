import os
from collections import defaultdict

import click
from flask import current_app
from flask.cli import with_appcontext


@click.command("route:list", help="Lists all routes of the Flask application.")
@click.argument("module_name", required=False)
@click.option(
    "--group",
    is_flag=True,
    help="Group routes by module when no specific module is provided.",
)
@with_appcontext
def route_list(module_name, group):
    base_path = os.path.join(os.getenv("WORKING_DIR", ""), "app/modules")

    # Checks if a module was specified and if it exists
    if module_name:
        module_path = os.path.join(base_path, module_name)
        if not os.path.exists(module_path):
            click.echo(click.style(f"Module '{module_name}' does not exist.", fg="red"))
            return
        click.echo(f"Listing routes for the '{module_name}' module...")
        # Path filtering for a specific module
        filtered_rules = [
            rule for rule in current_app.url_map.iter_rules() if rule.endpoint.startswith(f"{module_name}.")
        ]
        print_route_table(filtered_rules)
    else:
        if group:  # Group routes by module
            click.echo("Listing routes for all modules, grouped by module...")
            rules = sorted(current_app.url_map.iter_rules(), key=lambda rule: rule.endpoint)
            grouped_rules = defaultdict(list)
            for rule in rules:
                module = rule.endpoint.split(".")[0]
                grouped_rules[module].append(rule)

            for module, rules in sorted(grouped_rules.items()):
                click.echo(click.style(f"\nModule: {module}", fg="yellow"))
                print_route_table(rules)
        else:  # Lists all routes without grouping
            click.echo("Listing routes for all modules...")
            rules = sorted(current_app.url_map.iter_rules(), key=lambda rule: rule.endpoint)
            print_route_table(rules)


def print_route_table(rules):
    click.echo(f"{'Endpoint':<50} {'Methods':<30} {'Route':<100}")
    click.echo("-" * 180)
    for rule in rules:
        methods = ", ".join(sorted(rule.methods.difference({"HEAD", "OPTIONS"})))
        click.echo(f"{rule.endpoint:<50} {methods:<30} {rule.rule:<100}")
