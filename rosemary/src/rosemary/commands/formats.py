import click
from flask.cli import with_appcontext


@click.command(
    "formats:generate",
    help=(
        "Generate the missing download formats (Glencoe, DIMACS, SPLOT) for UVL "
        "models and process them in the queue. Use --force to regenerate all."
    ),
)
@click.option("--force", is_flag=True, help="Regenerate every format even if it already exists on disk.")
@click.option("--dataset", "dataset_id", type=int, default=None, help="Only process the hubfiles of this dataset id.")
@click.option(
    "--timeout", default=120, show_default=True, type=int, help="Timeout (in seconds) for each transform task."
)
@with_appcontext
def formats_generate(force, dataset_id, timeout):
    from app.features.flamapy.services import FlamapyService

    scope = f"dataset {dataset_id}" if dataset_id is not None else "all datasets"
    summary = FlamapyService().enqueue_missing_format_transforms(dataset_id=dataset_id, force=force, timeout=timeout)

    if summary["total"] == 0:
        click.echo(click.style("No hubfiles found for the given scope.", fg="yellow"))
        return

    click.echo(click.style(f"🔎 Checked {summary['total']} hubfiles ({scope}).", fg="cyan"))
    for hubfile_id, pending in summary["enqueued"]:
        click.echo(click.style(f"📤 Hubfile {hubfile_id} enqueued (missing: {', '.join(pending)})", fg="cyan"))
    for hubfile_id in summary["missing_source"]:
        click.echo(click.style(f"⚠️  Hubfile {hubfile_id} skipped — no UVL file on disk.", fg="yellow"))
    for hubfile_id, error in summary["failed"]:
        click.echo(click.style(f"❌ Hubfile {hubfile_id} could not be enqueued: {error}", fg="red"))

    click.echo("")
    click.echo(click.style(f"🎉 Enqueued {len(summary['enqueued'])} transform jobs.", fg="green"))
    if summary["up_to_date"]:
        click.echo(click.style(f"   {summary['up_to_date']} hubfiles already had every format.", fg="green"))
    if summary["missing_source"]:
        click.echo(
            click.style(f"   {len(summary['missing_source'])} hubfiles skipped (UVL missing on disk).", fg="yellow")
        )
    if summary["failed"]:
        click.echo(click.style(f"   {len(summary['failed'])} hubfiles could not be enqueued.", fg="red"))


@click.command("formats:pending", help="Show how many hubfiles are missing at least one download format.")
@click.option("--dataset", "dataset_id", type=int, default=None, help="Only check the hubfiles of this dataset id.")
@with_appcontext
def formats_pending(dataset_id):
    from app.features.flamapy.services import FlamapyService

    result = FlamapyService().count_hubfiles_missing_formats(dataset_id=dataset_id)

    if result["pending"] == 0:
        click.echo(click.style("✅ Every hubfile has all its download formats.", fg="green"))
    else:
        click.echo(
            click.style(f"⌛ {result['pending']} hubfiles are missing at least one download format.", fg="yellow")
        )
    if result["missing_source"]:
        click.echo(click.style(f"⚠️  {result['missing_source']} hubfiles have no UVL file on disk.", fg="yellow"))
