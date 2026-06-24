# cli/factlabel.py
import click
from flask.cli import with_appcontext

from app.features.factlabel.tasks import compute_factlabel


@click.command(
    "factlabel:generate",
    help="Generate FactLabels for hubfiles. By default, only missing ones. Use --force to regenerate all.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Delete all existing FactLabels and regenerate them.",
)
@click.option(
    "--light",
    is_flag=True,
    help="Generate light FactLabels (light_fact_label=True).",
)
@click.option(
    "--timeout",
    default=5,
    show_default=True,
    type=int,
    help="Timeout (in seconds) for each FactLabel task.",
)
@with_appcontext
def factlabel_generate(force, light, timeout):
    from app import db
    from app.features.factlabel.models import FactLabel
    from app.features.hubfile.models import Hubfile
    from app.managers.task_queue_manager import TaskQueueManager

    if force:
        click.echo(click.style("🗑️ Deleting all existing FactLabels...", fg="cyan"))
        updated = FactLabel.query.delete()
        db.session.commit()
        click.echo(click.style(f"✅ Cleared FactLabels for {updated} hubfiles.", fg="yellow"))

        hubfiles = Hubfile.query.all()
        click.echo(click.style(f"🔄 Regenerating FactLabels for {len(hubfiles)} hubfiles.", fg="cyan"))
    else:
        click.echo(click.style("🔎 Looking for hubfiles without FactLabel...", fg="cyan"))
        hubfiles = (
            Hubfile.query.outerjoin(FactLabel, FactLabel.hubfile_id == Hubfile.id)
            .filter((FactLabel.hubfile_id.is_(None)) | (FactLabel.factlabel_json == ""))
            .all()
        )

        if not hubfiles:
            click.echo(click.style("✅ All hubfiles already have FactLabels!", fg="green"))
            return

        click.echo(click.style(f"Found {len(hubfiles)} hubfiles missing FactLabels.", fg="yellow"))

    task_manager = TaskQueueManager()
    count_enqueued = 0

    for hubfile in hubfiles:
        try:
            task_manager.enqueue_task(
                compute_factlabel,
                hubfile_id=hubfile.id,
                light_fact_label=light,
                timeout=timeout,
            )
            count_enqueued += 1
            click.echo(click.style(f"📤 Hubfile {hubfile.id} enqueued for FactLabel (timeout={timeout}s)", fg="cyan"))
        except Exception as e:
            click.echo(click.style(f"❌ Could not enqueue Hubfile {hubfile.id}: {e}", fg="red"))

    click.echo(click.style(f"\n🎉 Enqueued {count_enqueued} jobs for FactLabel generation.", fg="green"))


# Nuevo comando: factlabel:pending
@click.command(
    "factlabel:pending",
    help="Show how many hubfiles are missing FactLabels.",
)
@with_appcontext
def factlabel_pending():
    from app.features.factlabel.models import FactLabel
    from app.features.hubfile.models import Hubfile

    missing = (
        Hubfile.query.outerjoin(FactLabel, FactLabel.hubfile_id == Hubfile.id)
        .filter((FactLabel.hubfile_id.is_(None)) | (FactLabel.factlabel_json == ""))
        .count()
    )

    if missing == 0:
        click.echo(click.style("✅ No pending FactLabels. All hubfiles are up to date!", fg="green"))
    else:
        click.echo(click.style(f"⌛ There are {missing} hubfiles pending FactLabel generation.", fg="yellow"))
