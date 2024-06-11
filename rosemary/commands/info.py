import click
import pkg_resources


def get_metadata_value(metadata_lines, key):
    default_value = f"{key}: Unknown"
    line = next((line for line in metadata_lines if line.startswith(key)), default_value)
    return line.split(':', 1)[1].strip() if line != default_value else default_value.split(':', 1)[1].strip()


@click.command()
def info():
    """Displays information about the Rosemary CLI."""
    distribution = pkg_resources.get_distribution("rosemary")

    try:
        metadata = distribution.get_metadata_lines('METADATA')
        author = get_metadata_value(metadata, 'Author')
        author_email = get_metadata_value(metadata, 'Author-email')
        description = get_metadata_value(metadata, 'Summary')
    except FileNotFoundError:
        author, author_email, description = "Unknown", "Unknown", "Not available"

    name = distribution.project_name
    version = distribution.version

    click.echo(f"Name: {name}")
    click.echo(f"Version: {version}")
    click.echo(f"Author: {author}")
    click.echo(f"Author-email: {author_email}")
    click.echo(f"Description: {description}")
