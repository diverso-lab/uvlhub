import click
from flask.cli import with_appcontext

from splent_framework.managers.feature_manager import FeatureManager


@click.command("feature:list", help="Lists features registered for the current app.")
@with_appcontext
def feature_list():
    app = click.get_current_context().obj
    features = FeatureManager(app, strict=False).get_features()

    click.echo(click.style(f"Features ({len(features)}):", fg="green"))
    for feature in features:
        click.echo(f"- {feature}")
