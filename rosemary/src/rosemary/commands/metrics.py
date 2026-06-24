"""CLI for the materialised `hubfile_metrics` table.

Two commands:

    rosemary metrics:status     # how many rows extracted vs. pending vs. errored
    rosemary metrics:backfill   # parse Hubfile.factlabel_json into hubfile_metrics

Backfill is idempotent: by default it only processes hubfiles that have a
fact label JSON but no (or stale) metrics row. Use --force to re-extract
every row, e.g. after bumping `EXTRACTOR_VERSION` or changing the schema.
"""

from __future__ import annotations

import click
from flask.cli import with_appcontext


@click.command(
    "metrics:status",
    help="Show how many hubfiles have extracted metrics vs. pending vs. errored.",
)
@with_appcontext
def metrics_status():
    from sqlalchemy import case, func

    from app import db
    from app.features.factlabel.metrics_extraction import EXTRACTOR_VERSION
    from app.features.factlabel.models import FactLabel, HubfileMetrics
    from app.features.hubfile.models import Hubfile

    total = db.session.query(func.count(Hubfile.id)).scalar() or 0
    with_factlabel = (
        db.session.query(func.count(FactLabel.hubfile_id))
        .filter(FactLabel.factlabel_json.isnot(None))
        .filter(FactLabel.factlabel_json != "")
        .scalar()
        or 0
    )

    metrics_total, metrics_ok, metrics_errored, metrics_stale = db.session.query(
        func.count(HubfileMetrics.hubfile_id),
        func.sum(case((HubfileMetrics.parse_error.is_(None), 1), else_=0)),
        func.sum(case((HubfileMetrics.parse_error.isnot(None), 1), else_=0)),
        func.sum(case((HubfileMetrics.extractor_version != EXTRACTOR_VERSION, 1), else_=0)),
    ).one()

    metrics_total = metrics_total or 0
    metrics_ok = metrics_ok or 0
    metrics_errored = metrics_errored or 0
    metrics_stale = metrics_stale or 0
    pending = with_factlabel - metrics_total

    click.echo(click.style("📊 Hubfile metrics status", fg="cyan", bold=True))
    click.echo(f"  Hubfiles total:           {total}")
    click.echo(f"  Hubfiles with factlabel:  {with_factlabel}")
    click.echo(f"  Metrics rows total:       {metrics_total}")
    click.echo(click.style(f"  ✅ OK rows:               {metrics_ok}", fg="green"))
    click.echo(click.style(f"  ⚠️  Errored rows:          {metrics_errored}", fg="yellow"))
    click.echo(click.style(f"  🕓 Stale (need re-extract): {metrics_stale}", fg="yellow"))
    click.echo(click.style(f"  ⏳ Pending extraction:    {pending}", fg="cyan"))


@click.command(
    "metrics:backfill",
    help=(
        "Extract hubfile_metrics from existing Hubfile.factlabel_json payloads. "
        "By default, only processes hubfiles missing a row or with stale "
        "extractor_version. Use --force to re-process every hubfile with a "
        "fact label."
    ),
)
@click.option(
    "--force",
    is_flag=True,
    help="Re-extract metrics for every hubfile that has a factlabel_json.",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Process at most N hubfiles. Useful for smoke-testing before a full run.",
)
@click.option(
    "--batch-size",
    type=int,
    default=200,
    show_default=True,
    help="Commit after N rows. Lower values trade throughput for memory.",
)
@with_appcontext
def metrics_backfill(force: bool, limit: int | None, batch_size: int):
    from app import db
    from app.features.factlabel.metrics_extraction import EXTRACTOR_VERSION, extract_metrics
    from app.features.factlabel.models import FactLabel, HubfileMetrics

    base = (
        db.session.query(FactLabel.hubfile_id, FactLabel.factlabel_json)
        .filter(FactLabel.factlabel_json.isnot(None))
        .filter(FactLabel.factlabel_json != "")
    )

    if not force:
        # Hubfiles with no metrics row, OR with one whose extractor_version
        # is older than the current. Stale rows happen when EXTRACTOR_VERSION
        # is bumped to fix an extraction bug — backfilling without --force
        # then refreshes them automatically.
        from sqlalchemy.orm import aliased

        hm = aliased(HubfileMetrics)
        base = base.outerjoin(hm, hm.hubfile_id == FactLabel.hubfile_id).filter(
            (hm.hubfile_id.is_(None)) | (hm.extractor_version != EXTRACTOR_VERSION)
        )

    if limit is not None:
        base = base.limit(limit)

    total = base.count() if limit is None else min(base.count(), limit)
    if total == 0:
        click.echo(
            click.style(
                "✅ Nothing to do. Every fact label already has a fresh metrics row.",
                fg="green",
            )
        )
        return

    click.echo(
        click.style(
            f"🔧 Backfilling metrics for {total} hubfile(s) (force={force}, batch={batch_size})…",
            fg="cyan",
        )
    )

    processed = ok = errored = failed = 0
    pending_in_batch = 0

    # Take the full id list up front: the yield_per cursor can't survive a
    # `rollback()` mid-iteration (MariaDB closes the unbuffered result),
    # and we need the option to rollback per-row when an INSERT fails
    # (e.g. a fact label reports a value that overflows a column). Ids are
    # small; loading 1e6 of them is still a handful of MB.
    ids_and_payloads = base.all()

    from datetime import datetime

    import pytz

    for hubfile_id, raw in ids_and_payloads:
        fields = extract_metrics(raw)
        try:
            row = db.session.get(HubfileMetrics, hubfile_id)
            if row is None:
                row = HubfileMetrics(hubfile_id=hubfile_id)
                db.session.add(row)

            row.extracted_at = datetime.now(pytz.utc)
            for column, value in fields.items():
                setattr(row, column, value)

            db.session.flush()
        except Exception as e:
            # Keep the whole backfill going when a single hubfile's payload
            # doesn't fit the schema — mark that one as errored and move on.
            db.session.rollback()
            failed += 1
            click.echo(click.style(f"  ✖ hubfile {hubfile_id}: {e}", fg="red"))
            # Store the failure in the row so `metrics:status` counts it.
            try:
                row = db.session.get(HubfileMetrics, hubfile_id) or HubfileMetrics(hubfile_id=hubfile_id)
                if hubfile_id not in {r.hubfile_id for r in db.session.new}:
                    db.session.add(row)
                row.extracted_at = datetime.now(pytz.utc)
                row.extractor_version = fields.get("extractor_version", "1")
                row.parse_error = f"db insert failed: {e}"[:2000]
                db.session.flush()
            except Exception:
                db.session.rollback()
            continue

        processed += 1
        pending_in_batch += 1
        if fields.get("parse_error"):
            errored += 1
        else:
            ok += 1

        if pending_in_batch >= batch_size:
            db.session.commit()
            pending_in_batch = 0
            click.echo(
                click.style(
                    f"  …{processed}/{total} processed (ok={ok}, errored={errored}, failed={failed})",
                    fg="cyan",
                )
            )

    if pending_in_batch or failed:
        db.session.commit()

    click.echo(
        click.style(
            f"\n🎉 Done. {processed} processed — {ok} OK, {errored} with parse errors, {failed} DB-insert failures.",
            fg="green",
        )
    )
