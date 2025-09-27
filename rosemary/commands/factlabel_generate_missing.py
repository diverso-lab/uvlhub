import click
from flask.cli import with_appcontext


@click.command(
    "factlabel:generate-missing",
    help="Enqueue tasks to generate FactLabels for all Hubfiles that do not have one yet.",
)
@with_appcontext
def factlabel_generate_missing():
    from app.modules.hubfile.models import Hubfile
    from core.managers.task_queue_manager import TaskQueueManager

    click.echo(click.style("🔎 Looking for hubfiles without FactLabel...", fg="cyan"))

    missing = Hubfile.query.filter((Hubfile.factlabel_json.is_(None)) | (Hubfile.factlabel_json == "")).all()

    if not missing:
        click.echo(click.style("✅ All hubfiles already have FactLabels!", fg="green"))
        return

    click.echo(click.style(f"Found {len(missing)} hubfiles missing FactLabels.", fg="yellow"))

    task_manager = TaskQueueManager()
    count_enqueued = 0

    for hubfile in missing:
        try:
            task_manager.enqueue_task(
                "app.modules.hubfile.tasks.compute_factlabel",
                hubfile_id=hubfile.id,
                timeout=1,
            )
            count_enqueued += 1
            click.echo(click.style(f"📤 Hubfile {hubfile.id} enqueued for FactLabel", fg="cyan"))
        except Exception as e:
            click.echo(click.style(f"❌ Could not enqueue Hubfile {hubfile.id}: {e}", fg="red"))

    click.echo(click.style(f"\n🎉 Enqueued {count_enqueued} jobs for FactLabel generation.", fg="green"))
