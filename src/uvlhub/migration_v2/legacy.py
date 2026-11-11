"""E6, legacy: the history of use, the URLs that change, and the notices
held until RB-2 ends (§2.1, §5.5, §5.7, §7.2).

- usage_daily (DM-5): v2.12's view and download records, by dataset or
  file, kind and day, counting distinct visitors: an account, a browser's
  cookie when nobody signed in, each record when it has neither. A
  record's owner, a dataset not published and a record without its target
  or its date are not counted, and counts says how many of each. The raw
  records do not pass (A12-09). E6 aggregates them in the outputs and
  loads them into statistics' usage_daily, source legacy_v2, which the
  dashboard shows next to 3.0's own (DC-8), with the public note that says
  why the figures went down in usage_note, until the day before T0. The
  report's dm5 puts the counters v2.12 showed and the aggregates side by
  side, with the same note (A10-05, A10-06).

- legacy_url (CO-2): every address of v2.12 that answers somewhere else
  now, through legacy_urls' own import (splent feature:legacy_urls import,
  in a process of its own, as E8 runs storage-migrate): v2.12's
  doi_mapping, each chain followed to the DOI a dataset of 3.0 has, as a
  308 (C-20). dataset still redirects by its own doi_mapping, so those
  mappings load there too: a cycle, or a chain that ends at a DOI no
  dataset has, is a conflict and loads nowhere. The /hubfiles/raw/<id>/
  <name> of a file DM-10 renamed is hubfile's alias (E8), whose 308
  answers before any 404 would.
- the notices of the move (§5.5, §5.7, D13 b), which wait for the end of
  RB-2, as a rollback would make them false: to both parties of every
  offer E5 cancelled, and to every account with a key carried over, saying
  until when it works or why it was carried over revoked. They go into
  mail's outbox held, under the tag --hold-tag (rb2), from MAIL_FROM, in
  English and Spanish (MIG-09), with no link that carries a token: nothing
  sends them until splent feature:mail release --tag rb2. held_notice, in
  the outputs, says what each one is about.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import sqlalchemy as sa

from uvlhub.migration_v2.content import PUBLISHED
from uvlhub.migration_v2.db import (
    all_rows,
    insert_batches,
    qualified,
    reflect,
)
from uvlhub.migration_v2.ledger import HELD, stop_on_conflicts
from uvlhub.migration_v2.schema import child_env, run_child

# The records of v2.12 (§7.2): table, what it counts, the kind, and its
# columns for the target, the moment and the cookie.
USAGE = (
    ("ds_view_record", "dataset", "view", "dataset_id", "view_date", "view_cookie"),
    (
        "ds_download_record",
        "dataset",
        "download",
        "dataset_id",
        "download_date",
        "download_cookie",
    ),
    ("hubfile_view_record", "hubfile", "view", "file_id", "view_date", "view_cookie"),
    (
        "hubfile_download_record",
        "hubfile",
        "download",
        "file_id",
        "download_date",
        "download_cookie",
    ),
)
LEGACY_SOURCE = "legacy_v2"
# A permanent redirect that keeps the method (C-20, CO-2).
PERMANENT = 308
# The state of a mail of mail's outbox that waits for its batch's release.
HELD_MAIL = "held"

TOKEN_REVOKED = {
    "import_no_scopes": (
        "it allowed nothing (it had no scopes)",
        "no permitía nada (no tenía permisos)",
    ),
    "import_never_used": ("it was never used", "nunca se usó"),
    "import_unused": (
        "it had not been used for a year",
        "llevaba un año sin usarse",
    ),
}


# ── Usage (DM-5) ─────────────────────────────────────────────────────────


def _usage_from(params, table, target_type, target):
    """The records of ``table`` joined to what they count in uvlhub3: d is
    the dataset, loaded or not (NULL)."""
    src = qualified(params.source_schema, table)
    datasets = qualified(params.target_schema, "datasets")
    if target_type == "dataset":
        return f"FROM {src} r LEFT JOIN {datasets} d ON d.id = r.{target}"
    hubfiles = qualified(params.target_schema, "hubfiles")
    return (
        f"FROM {src} r LEFT JOIN {hubfiles} h ON h.id = r.{target} "
        f"LEFT JOIN {datasets} d ON d.id = h.dataset_id"
    )


def aggregate_usage(ctx, connection) -> dict:
    """usage_daily from every record table, and why each record that is
    not in it is not, by table."""
    params = ctx.params
    published = ", ".join(f"'{status}'" for status in PUBLISHED)
    usage = qualified(params.work_schema, "usage_daily")
    found = {}
    for table, target_type, kind, target, date, cookie in USAGE:
        joined = _usage_from(params, table, target_type, target)
        counted = (
            f"r.{target} IS NOT NULL AND r.{date} IS NOT NULL AND d.id IS NOT NULL "
            f"AND d.status IN ({published}) "
            "AND (r.user_id IS NULL OR r.user_id <> d.user_id)"
        )
        with connection.begin():
            days = connection.execute(
                sa.text(
                    f"INSERT INTO {usage} "
                    "(target_type, target_id, kind, day, visitors, records, source) "
                    f"SELECT :type, r.{target}, :kind, DATE(r.{date}), "
                    "COUNT(DISTINCT COALESCE(CONCAT('u:', r.user_id), "
                    f"CONCAT('c:', BINARY r.{cookie}), CONCAT('r:', r.id))), "
                    f"COUNT(*), :source {joined} WHERE {counted} "
                    f"GROUP BY r.{target}, DATE(r.{date})"
                ),
                {"type": target_type, "kind": kind, "source": LEGACY_SOURCE},
            ).rowcount
        reasons = connection.execute(
            sa.text(
                "SELECT COUNT(*) AS total, "
                f"SUM(r.{target} IS NULL) AS no_target, "
                f"SUM(r.{target} IS NOT NULL AND r.{date} IS NULL) AS no_date, "
                f"SUM(r.{target} IS NOT NULL AND r.{date} IS NOT NULL "
                "AND d.id IS NULL) AS not_loaded, "
                f"SUM(r.{date} IS NOT NULL AND d.id IS NOT NULL "
                f"AND d.status NOT IN ({published})) AS not_published, "
                f"SUM(r.{date} IS NOT NULL AND d.status IN ({published}) "
                "AND r.user_id = d.user_id) AS owner, "
                f"SUM({counted}) AS aggregated "
                f"{joined}"
            )
        ).one()
        connection.rollback()
        counts = {key: int(value or 0) for key, value in reasons._mapping.items()}
        ctx.ledger.count(
            table,
            counts.pop("total"),
            counts.pop("aggregated"),
            dict(counts, days=days),
        )
        found[table] = days
    return found


def dm5(ctx, connection) -> dict:
    """The counters v2.12 showed next to what its records give, and the
    note that says why they differ, for the hub to publish (DM-5)."""
    totals = defaultdict(lambda: {"visitors": 0, "records": 0})
    rows = connection.execute(
        sa.text(
            "SELECT target_type, kind, SUM(visitors) AS visitors, SUM(records) AS records "
            f"FROM {qualified(ctx.params.work_schema, 'usage_daily')} "
            "GROUP BY target_type, kind"
        )
    ).all()
    for target_type, kind, visitors, records in rows:
        totals[f"{target_type}_{kind}s"] = {
            "visitors": int(visitors),
            "records": int(records),
        }
    counters = ctx.facts.get("statistics_v2") or [{}]
    shown = counters[0]
    views = totals["dataset_views"]["visitors"]
    downloads = totals["dataset_downloads"]["visitors"]
    note = (
        f"Use before {ctx.params.t0:%d %B %Y} comes from uvlhub.io 2.12 as daily "
        "figures: one visitor a day per account, or per browser when nobody "
        "signed in, without the owner's own visits and without drafts. "
        "uvlhub.io 2.12 counted every request, some twice and some not at all, "
        f"and showed {shown.get('datasets_viewed') or 0} views and "
        f"{shown.get('datasets_downloaded') or 0} downloads of datasets; its "
        f"records give {views} daily visitors and {downloads} daily downloaders."
    )
    return {"v2_12_counters": counters, "aggregated": dict(totals), "note": note}


def load_usage(ctx, connection, note: str) -> int:
    """statistics' usage_daily from E6's aggregates, and its usage_note,
    the note of DM-5 until the day before T0. How many days went in."""
    params = ctx.params
    target = params.target_schema
    if connection.in_transaction():
        connection.commit()
    with connection.begin():
        days = connection.execute(
            sa.text(
                f"INSERT INTO {qualified(target, 'usage_daily')} "
                "(target_type, target_id, kind, day, source, visitors, records) "
                "SELECT target_type, target_id, kind, day, source, visitors, records "
                f"FROM {qualified(params.work_schema, 'usage_daily')} "
                "ORDER BY target_type, target_id, kind, day"
            )
        ).rowcount
        connection.execute(
            sa.text(
                f"INSERT INTO {qualified(target, 'usage_note')} (source, note, until) "
                "VALUES (:source, :note, :until)"
            ),
            {
                "source": LEGACY_SOURCE,
                "note": note,
                "until": (params.t0 - timedelta(days=1)).date(),
            },
        )
    return days


# ── Legacy URLs (CO-2, C-20) ─────────────────────────────────────────────


def follow_mappings(mappings, served):
    """C-20: v2.12's doi_mapping, each chain followed to its end.

    ``mappings`` are the rows, in id order; ``served`` the DOIs a dataset of
    3.0 answers. Answers (loads, shadowed, cycles, dangling): the rows that
    load, each with dataset_doi_new the end of its chain; the rows another
    row of the same old DOI hides, as v2.12's lookup found the first;
    every cycle, as its rows; and the rows whose chain ends at a DOI no
    dataset has, or runs into a cycle.
    """
    first = {}
    shadowed = []
    for row in mappings:
        old, new = row["dataset_doi_old"], row["dataset_doi_new"]
        if not old or not new:
            shadowed.append((row, None))
            continue
        if old in first:
            shadowed.append((row, first[old]["id"]))
            continue
        first[old] = row
    loads, cycles, dangling, in_cycle = [], [], [], set()
    for old, row in first.items():
        seen, doi = [old], row["dataset_doi_new"]
        while doi in first and doi not in seen:
            seen.append(doi)
            doi = first[doi]["dataset_doi_new"]
        if doi in seen:
            cycle = frozenset(seen[seen.index(doi) :])
            if old not in cycle:
                # It runs into a cycle, and ends nowhere.
                dangling.append(row)
            elif cycle not in in_cycle:
                in_cycle.add(cycle)
                cycles.append([first[d] for d in sorted(cycle)])
            continue
        if doi not in served:
            dangling.append(row)
            continue
        loads.append(dict(row, dataset_doi_new=doi))
    return loads, shadowed, cycles, dangling


def legacy_urls(ctx, connection, tgt):
    """doi_mapping loaded and legacy_url written: (the mappings loaded,
    how many URLs)."""
    params, ledger = ctx.params, ctx.ledger
    src = reflect(connection, params.source_schema, only=["doi_mapping"])
    mappings = all_rows(connection, src["doi_mapping"])
    served = set(
        connection.execute(
            sa.text(
                f"SELECT m.dataset_doi FROM {qualified(params.target_schema, 'ds_meta_data')} m "
                f"JOIN {qualified(params.target_schema, 'datasets')} d "
                "ON d.ds_meta_data_id = m.id WHERE m.dataset_doi IS NOT NULL"
            )
        ).scalars()
    )
    connection.rollback()
    loads, shadowed, cycles, dangling = follow_mappings(mappings, served)
    for row, by in shadowed:
        ledger.drop(
            "doi_mapping",
            row["id"],
            "shadowed" if by else "incomplete",
            f"doi_mapping {by} maps the same DOI" if by else "a DOI is missing",
        )
    for cycle in cycles:
        ledger.conflict(
            "doi_mapping_cycle",
            "doi_mapping",
            cycle[0]["dataset_doi_old"],
            cycle,
            detail=" -> ".join(row["dataset_doi_old"] for row in cycle),
        )
        for row in cycle:
            ledger.drop("doi_mapping", row["id"], HELD, "doi_mapping_cycle")
    for row in dangling:
        ledger.conflict(
            "doi_mapping_dangling",
            "doi_mapping",
            row["dataset_doi_old"],
            [row],
            detail="its chain does not end at a DOI a dataset of 3.0 has",
        )
        ledger.drop("doi_mapping", row["id"], HELD, "doi_mapping_dangling")
    insert_batches(connection, tgt["doi_mapping"], loads)
    followed = {row["id"]: row for row in mappings}
    ledger.note(
        "doi_mapping: chains followed to their end",
        sum(
            1
            for row in loads
            if row["dataset_doi_new"] != followed[row["id"]]["dataset_doi_new"]
        ),
    )
    ledger.count("doi_mapping", len(mappings), len(loads))

    urls = [
        {
            "path": f"/doi/{row['dataset_doi_old']}/",
            "target": f"/doi/{row['dataset_doi_new']}/",
            "status": PERMANENT,
            "ref": f"doi_mapping:{row['id']}",
        }
        for row in loads
    ]
    imported = import_legacy_urls(ctx, connection, urls)
    return loads, imported


def import_legacy_urls(ctx, connection, urls) -> int:
    """``urls`` into legacy_urls' table by its import, from a JSON file of
    their own, every row or none; their dates are T0 (principle 2). How
    many it holds then."""
    params = ctx.params
    if not urls:
        return 0
    folder = Path(tempfile.mkdtemp(prefix="migration_v2_legacy_urls_"))
    try:
        source = folder / "legacy_urls.json"
        source.write_text(json.dumps(urls, ensure_ascii=False), encoding="utf-8")
        output = run_child(
            "E6", list(params.legacy_urls_command) + [str(source)], child_env(params)
        )
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    ctx.facts["legacy_urls_import_output"] = output.strip().splitlines()[-5:]
    table = qualified(params.target_schema, "legacy_url")
    if connection.in_transaction():
        connection.commit()
    with connection.begin():
        connection.execute(
            sa.text(f"UPDATE {table} SET created_at = :t0, updated_at = :t0"),
            {"t0": params.t0},
        )
        return connection.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar()


# ── Held notices (§5.5, §5.7) ────────────────────────────────────────────


def _transfer_notices(ctx, connection):
    """D13 b: both parties of every offer E5 cancelled."""
    cancelled = ctx.facts.get("transfers_cancelled") or []
    if not cancelled:
        return []
    t = ctx.params.target_schema
    rows = connection.execute(
        sa.text(
            "SELECT o.id, o.created_at, m.title, m.dataset_doi, "
            "o.from_user_id, f.email AS from_email, o.to_user_id, r.email AS to_email "
            f"FROM {qualified(t, 'dataset_transfer_request')} o "
            f"JOIN {qualified(t, 'datasets')} d ON d.id = o.dataset_id "
            f"JOIN {qualified(t, 'ds_meta_data')} m ON m.id = d.ds_meta_data_id "
            f"JOIN {qualified(t, 'user')} f ON f.id = o.from_user_id "
            f"JOIN {qualified(t, 'user')} r ON r.id = o.to_user_id "
            "WHERE o.id IN :ids ORDER BY o.id"
        ).bindparams(sa.bindparam("ids", expanding=True)),
        {"ids": cancelled},
    ).all()
    moved = f"{ctx.params.t0:%Y-%m-%d}"
    notices = []
    for row in rows:
        named = f"“{row.title}”" + (f" ({row.dataset_doi})" if row.dataset_doi else "")
        notices.append(
            (
                "transfer_cancelled",
                f"dataset_transfer_request:{row.id}",
                row.from_user_id,
                row.from_email,
                f"Your offer to transfer {named} was cancelled",
                f"uvlhub.io moved to uvlhub 3.0 on {moved}. The offers to transfer "
                "a dataset that were still waiting for an answer then were "
                f"cancelled, and yours of {named}, made on "
                f"{row.created_at:%Y-%m-%d}, is one of them. The dataset is still "
                "yours. To hand it over, make the offer again from its page.\n\n"
                f"uvlhub.io pasó a uvlhub 3.0 el {moved}. Las ofertas de "
                "transferencia de un dataset que seguían sin respuesta entonces se "
                f"cancelaron, y la tuya de {named}, del "
                f"{row.created_at:%Y-%m-%d}, es una de ellas. El dataset sigue "
                "siendo tuyo. Para cederlo, vuelve a ofrecerlo desde su página.",
            )
        )
        notices.append(
            (
                "transfer_cancelled",
                f"dataset_transfer_request:{row.id}",
                row.to_user_id,
                row.to_email,
                f"The offer of {named} to you was cancelled",
                f"uvlhub.io moved to uvlhub 3.0 on {moved}. The offers to transfer "
                "a dataset that were still waiting for an answer then were "
                f"cancelled, and the one of {named} to you, made on "
                f"{row.created_at:%Y-%m-%d}, is one of them. If you still want it, "
                "ask its owner to offer it to you again.\n\n"
                f"uvlhub.io pasó a uvlhub 3.0 el {moved}. Las ofertas de "
                "transferencia de un dataset que seguían sin respuesta entonces se "
                f"cancelaron, y la de {named} para ti, del "
                f"{row.created_at:%Y-%m-%d}, es una de ellas. Si aún lo quieres, "
                "pide a su dueño que te lo vuelva a ofrecer.",
            )
        )
    return notices


def _token_notices(ctx, connection):
    """§5.5: one notice per account with keys carried over, each key with
    until when it works, or why it was carried over revoked."""
    t = ctx.params.target_schema
    rows = connection.execute(
        sa.text(
            "SELECT k.user_id, u.email, k.name, k.expires_at, k.revoked_at, "
            f"k.revoked_reason FROM {qualified(t, 'api_token')} k "
            f"JOIN {qualified(t, 'user')} u ON u.id = k.user_id ORDER BY k.user_id, k.id"
        )
    ).all()
    keys = defaultdict(list)
    for row in rows:
        keys[(row.user_id, row.email)].append(row)
    moved = f"{ctx.params.t0:%Y-%m-%d}"
    notices = []
    for (user_id, email), tokens in sorted(keys.items(), key=lambda item: item[0][0]):
        english, spanish = [], []
        for token in tokens:
            if token.revoked_at is not None:
                why_en, why_es = TOKEN_REVOKED.get(
                    token.revoked_reason, ("it was revoked", "se revocó")
                )
                english.append(f"- {token.name}: revoked, as {why_en}.")
                spanish.append(f"- {token.name}: revocada, porque {why_es}.")
            else:
                english.append(
                    f"- {token.name}: works until {token.expires_at:%Y-%m-%d}."
                )
                spanish.append(
                    f"- {token.name}: funciona hasta el {token.expires_at:%Y-%m-%d}."
                )
        notices.append(
            (
                "api_keys_carried_over",
                f"user:{user_id}",
                user_id,
                email,
                "Your uvlhub API keys after the move to uvlhub 3.0",
                f"uvlhub.io moved to uvlhub 3.0 on {moved}, and your API keys came "
                "along. They are sent as before, in X-API-Key, and they now expire:\n\n"
                + "\n".join(english)
                + "\n\nA new key can be made from your account once it expires or "
                "if one was revoked.\n\n"
                f"uvlhub.io pasó a uvlhub 3.0 el {moved}, y tus claves de API se "
                "vinieron con él. Se envían como antes, en X-API-Key, y ahora "
                "caducan:\n\n"
                + "\n".join(spanish)
                + "\n\nPuedes crear una clave nueva desde tu cuenta cuando caduque o "
                "si alguna se revocó.",
            )
        )
    return notices


def held_notices(ctx, connection, tgt) -> int:
    """The notices into mail's outbox, held under the hold tag until RB-2
    ends, and held_notice with what each one is about."""
    params = ctx.params
    notices = _transfer_notices(ctx, connection) + _token_notices(ctx, connection)
    connection.rollback()
    mails, about = [], []
    for kind, ref, user_id, email, subject, body in notices:
        if not email:
            ctx.ledger.note(f"held_notice: {kind} for an account without an address")
            continue
        outbox_id = len(mails) + 1
        mails.append(
            {
                "id": outbox_id,
                "recipients": email,
                "sender": params.mail_from,
                "reply_to": None,
                "subject": subject,
                "body_text": body,
                "body_html": None,
                # Kept whole: it carries no link, and is sent from its row.
                "retryable": True,
                "state": HELD_MAIL,
                "hold_tag": params.hold_tag,
                "attempts": 0,
                "last_error": None,
                "created_at": params.t0,
                "last_attempt_at": None,
                "sent_at": None,
            }
        )
        about.append(
            {
                "id": outbox_id,
                "outbox_id": outbox_id,
                "kind": kind,
                "ref": ref,
                "user_id": user_id,
            }
        )
    insert_batches(connection, tgt["mail_outbox"], mails)
    insert_batches(connection, ctx.outputs["held_notice"], about)
    return len(mails)


def legacy(ctx) -> None:
    params = ctx.params
    with ctx.engine.connect() as connection:
        tgt = reflect(
            connection, params.target_schema, only=["doi_mapping", "mail_outbox"]
        )
        connection.rollback()
        days = aggregate_usage(ctx, connection)
        loads, urls = legacy_urls(ctx, connection, tgt)
        notices = held_notices(ctx, connection, tgt)
        ctx.facts["dm5"] = dm5(ctx, connection)
        loaded_days = load_usage(ctx, connection, ctx.facts["dm5"]["note"])
        connection.rollback()
    ctx.loaded["doi_mapping"] = {row["id"] for row in loads}
    ctx.ledger.count("usage_daily", sum(days.values()), loaded_days)
    ctx.facts["legacy"] = {
        "usage_daily": days,
        "doi_mapping": len(loads),
        "legacy_url": urls,
        "held_notice": notices,
        "hold_tag": params.hold_tag,
    }
    stop_on_conflicts(ctx, "E6")
