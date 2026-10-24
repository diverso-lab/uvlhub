"""E7, post-load: counters with their margin, every foreign key, the counts
and the checks of §9.2 (V-*).

A check is blocking or not. Blocking ones stop the run when they fail. The
ones that depend on what the final E5 does (V-09, a lineage repaired by
concept DOI) are reported and do not block in this first pass.
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa

from splent_io.splent_feature_auth.models import canonical_email

from uvlhub_splent.migration_v2 import contract as contract_module
from uvlhub_splent.migration_v2 import rules
from uvlhub_splent.migration_v2.db import qualified, quote
from uvlhub_splent.migration_v2.ledger import to_json
from uvlhub_splent.migration_v2.params import Refused

# The tables whose ids are kept, and the source table each one's come from.
KEPT_IDS = {
    "user": "user",
    "user_profile": "user_profile",
    "external_identity": "external_identity",
    "api_token": "api_keys",
    "ds_metrics": "ds_metrics",
    "ds_meta_data": "ds_meta_data",
    "datasets": "datasets",
    "author": "author",
    "feature_model": "feature_model",
    "hubfiles": "hubfiles",
    "dataset_rating": "dataset_rating",
    "dataset_transfer_request": "dataset_transfer_request",
}
# V-01: the source tables whose every row is accounted for, the target
# table it loads into, and the other entities a row may be mapped to.
ACCOUNTED = {
    "user": "user",
    "user_profile": "user_profile",
    "external_identity": "external_identity",
    "api_keys": "api_token",
    "ds_metrics": "ds_metrics",
    "ds_meta_data": "ds_meta_data",
    "datasets": "datasets",
    "author": "author",
    "feature_model": "feature_model",
    "hubfiles": "hubfiles",
    "dataset_rating": "dataset_rating",
    "dataset_transfer_request": "dataset_transfer_request",
    "orcid": None,
    "github": None,
}


@dataclass
class Check:
    name: str
    ok: bool
    blocking: bool = True
    detail: object = None

    def as_row(self) -> dict:
        return {
            "name": self.name,
            "ok": self.ok,
            "blocking": self.blocking,
            "detail": None if self.detail is None else to_json(self.detail),
        }


def set_counters(ctx, connection) -> dict[str, int]:
    """§4.1: every table with kept ids starts at C3. Answers C3 by table."""
    params = ctx.params
    given = {}
    for target, source in KEPT_IDS.items():
        max_id = connection.execute(
            sa.text(f"SELECT MAX(id) FROM {qualified(params.target_schema, target)}")
        ).scalar()
        c3 = rules.next_counter(
            ctx.source_counters.get(source), max_id, params.id_margin, params.id_round
        )
        connection.exec_driver_sql(
            f"ALTER TABLE {qualified(params.target_schema, target)} AUTO_INCREMENT = {int(c3)}"
        )
        given[target] = c3
    connection.commit()
    return given


def v03_counters(connection, schema, given) -> Check:
    rows = dict(
        connection.execute(
            sa.text(
                "SELECT table_name, auto_increment FROM information_schema.tables "
                "WHERE table_schema = :s"
            ),
            {"s": schema},
        ).all()
    )
    short = {t: (rows.get(t), c3) for t, c3 in given.items() if (rows.get(t) or 0) < c3}
    return Check("V-03", not short, detail=short or given)


def foreign_key_orphans(connection, schema) -> dict[str, int]:
    """V-04: rows whose foreign key names no parent, by constraint. One
    query per foreign key, generated as the plan does: MariaDB does not
    check again when FOREIGN_KEY_CHECKS comes back on."""
    keys = connection.execute(
        sa.text(
            "SELECT table_name, column_name, referenced_table_name, referenced_column_name "
            "FROM information_schema.key_column_usage "
            "WHERE table_schema = :s AND referenced_table_name IS NOT NULL "
            "ORDER BY table_name, column_name"
        ),
        {"s": schema},
    ).all()
    found = {}
    for table, column, parent, parent_column in keys:
        orphans = connection.execute(
            sa.text(
                f"SELECT COUNT(*) FROM {qualified(schema, table)} c "
                f"LEFT JOIN {qualified(schema, parent)} p ON p.{quote(parent_column)} = c.{quote(column)} "
                f"WHERE c.{quote(column)} IS NOT NULL AND p.{quote(parent_column)} IS NULL"
            )
        ).scalar()
        if orphans:
            found[f"{table}.{column} -> {parent}"] = orphans
    return found


def empty_tables(connection, schema, contract) -> dict[str, int]:
    """The tables the contract says the migration leaves empty, that are not."""
    found = {}
    for table in contract.by_role(contract_module.EMPTY):
        rows = connection.execute(
            sa.text(f"SELECT COUNT(*) FROM {qualified(schema, table.name)}")
        ).scalar()
        if rows:
            found[table.name] = rows
    return found


def v01_accounted(ctx, connection) -> Check:
    """V-01: every row of the source is loaded with its id, dropped with a
    reason, or mapped to where it went. Answers the ones that are none."""
    params = ctx.params
    ledger = ctx.ledger
    missing = {}
    for source, target in ACCOUNTED.items():
        ids = connection.execute(
            sa.text(f"SELECT id FROM {qualified(params.source_schema, source)}")
        ).scalars()
        loaded = set()
        if target is not None:
            loaded = set(
                connection.execute(
                    sa.text(f"SELECT id FROM {qualified(params.target_schema, target)}")
                ).scalars()
            )
        lost = [
            i
            for i in ids
            if i not in loaded
            and (source, i) not in ledger.dropped
            and (source, i) not in ledger.id_map
        ]
        if lost:
            missing[source] = lost[:20]
    return Check("V-01", not missing, detail=missing or None)


def v02_dois(ctx, connection) -> Check:
    """V-02: every DOI of the source is a dataset of 3.0, a tombstone, or
    dropped with its metadata. 3.0 keeps the DOI in ds_meta_data (no pid
    yet, D14), so that is where it is looked for, byte for byte."""
    p = ctx.params
    lost = connection.execute(
        sa.text(
            f"SELECT m.dataset_doi FROM {qualified(p.source_schema, 'ds_meta_data')} m "
            "WHERE m.dataset_doi IS NOT NULL AND m.dataset_doi <> '' "
            f"AND NOT EXISTS (SELECT 1 FROM {qualified(p.target_schema, 'ds_meta_data')} t "
            f"  JOIN {qualified(p.target_schema, 'datasets')} d ON d.ds_meta_data_id = t.id "
            "  WHERE BINARY t.dataset_doi = BINARY m.dataset_doi) "
            f"AND NOT EXISTS (SELECT 1 FROM {qualified(p.work_schema, 'tombstone')} z "
            "  WHERE BINARY z.doi = BINARY m.dataset_doi) "
            f"AND NOT EXISTS (SELECT 1 FROM {qualified(p.work_schema, 'dropped')} x "
            "  WHERE x.entity = 'ds_meta_data' AND x.ref_id = m.id)"
        )
    ).scalars()
    lost = list(lost)
    return Check("V-02", not lost, detail=lost or None)


def v05_admins(ctx, connection) -> Check:
    rows = connection.execute(
        sa.text(
            f"SELECT id, email, role FROM {qualified(ctx.params.target_schema, 'user')} WHERE role <> 'user'"
        )
    ).all()
    allowed = {canonical_email(e) for e in ctx.params.admin_emails}
    stray = [
        f"{r.id} {r.email} {r.role}"
        for r in rows
        if canonical_email(r.email) not in allowed
    ]
    return Check(
        "V-05",
        not stray,
        detail={
            "admins": [r.id for r in rows],
            "stray": stray,
            "listed_not_loaded": ctx.facts.get("admins_missing"),
        },
    )


def v06_tokens(ctx, connection) -> Check:
    p = ctx.params
    wrong = connection.execute(
        sa.text(
            f"SELECT COUNT(*) FROM {qualified(p.source_schema, 'api_keys')} k "
            f"JOIN {qualified(p.target_schema, 'api_token')} t ON t.id = k.id "
            "WHERE t.token_hash <> SHA2(k.`key`, 256) OR BINARY t.prefix <> BINARY LEFT(k.`key`, 15) "
            "OR t.user_id <> k.user_id"
        )
    ).scalar()
    return Check("V-06", not wrong, detail=wrong or None)


def v07_identities(ctx, connection) -> Check:
    p = ctx.params
    doubled = connection.execute(
        sa.text(
            f"SELECT user_id, provider, COUNT(*) n FROM {qualified(p.target_schema, 'external_identity')} "
            "GROUP BY user_id, provider HAVING n > 1"
        )
    ).all()
    unaccounted = [
        f"{table} {row_id}"
        for table in ("orcid", "github")
        for row_id in connection.execute(
            sa.text(f"SELECT id FROM {qualified(p.source_schema, table)}")
        ).scalars()
        if (table, row_id) not in ctx.ledger.id_map
        and (table, row_id) not in ctx.ledger.dropped
    ]
    return Check(
        "V-07",
        not doubled and not unaccounted,
        detail={"doubled": [tuple(r) for r in doubled], "unaccounted": unaccounted}
        if doubled or unaccounted
        else None,
    )


def v09_lineages(ctx, connection) -> Check:
    p = ctx.params
    branches = connection.execute(
        sa.text(
            f"SELECT dataset_origin_id FROM {qualified(p.target_schema, 'datasets')} "
            "WHERE dataset_origin_id IS NOT NULL GROUP BY dataset_origin_id HAVING COUNT(*) > 1"
        )
    ).scalars()
    branches = list(branches)
    # Advisory in this pass: the repair by concept DOI is the final E5's.
    return Check("V-09", not branches, blocking=False, detail=branches or None)


def v10_votes(ctx, connection) -> Check:
    p = ctx.params
    off_root = connection.execute(
        sa.text(
            f"SELECT COUNT(*) FROM {qualified(p.target_schema, 'dataset_rating')} r "
            f"JOIN {qualified(p.target_schema, 'datasets')} d ON d.id = r.dataset_id "
            "WHERE d.dataset_origin_id IS NOT NULL"
        )
    ).scalar()
    return Check("V-10", not off_root, detail=off_root or None)


def v11_copied(ctx, connection) -> Check:
    """V-11: the columns copied as they are, compared exactly, NULL-safe.
    The takeover candidates' passwords are not copied on purpose (C-28)."""
    p = ctx.params
    skip = sorted(ctx.takeover_users) or [0]
    users = connection.execute(
        sa.text(
            f"SELECT s.id FROM {qualified(p.source_schema, 'user')} s "
            f"JOIN {qualified(p.target_schema, 'user')} t USING (id) "
            "WHERE NOT (BINARY s.email <=> BINARY t.email AND s.created_at <=> t.created_at "
            "AND (BINARY s.password <=> BINARY t.password OR s.id IN :skip))"
        ).bindparams(sa.bindparam("skip", expanding=True)),
        {"skip": skip},
    ).scalars()
    files = connection.execute(
        sa.text(
            f"SELECT s.id FROM {qualified(p.source_schema, 'hubfiles')} s "
            f"JOIN {qualified(p.target_schema, 'hubfiles')} t USING (id) "
            "WHERE NOT (BINARY s.name <=> BINARY t.name AND BINARY s.directory_path <=> BINARY t.directory_path "
            "AND BINARY s.checksum <=> BINARY t.checksum AND s.size <=> t.size AND s.dataset_id <=> t.dataset_id)"
        )
    ).scalars()
    users, files = list(users), list(files)
    return Check(
        "V-11",
        not users and not files,
        detail={"user": users, "hubfiles": files} if users or files else None,
    )


def v15_accounts(ctx, connection) -> Check:
    """V-15: no seed account loaded, and every probable takeover unconfirmed
    with a password nobody knows."""
    p = ctx.params
    seeds = list(
        connection.execute(
            sa.text(
                f"SELECT id FROM {qualified(p.target_schema, 'user')} WHERE email LIKE :seed"
            ),
            {"seed": "%" + rules.SEED_EMAIL_SUFFIX},
        ).scalars()
    )
    takeovers = sorted(ctx.takeover_users) or [0]
    open_ = list(
        connection.execute(
            sa.text(
                f"SELECT id FROM {qualified(p.target_schema, 'user')} WHERE id IN :ids "
                "AND (email_verified_at IS NOT NULL OR has_usable_password OR BINARY password <> BINARY :unusable)"
            ).bindparams(sa.bindparam("ids", expanding=True)),
            {"ids": takeovers, "unusable": rules.UNUSABLE_PASSWORD},
        ).scalars()
    )
    return Check(
        "V-15",
        not seeds and not open_,
        detail={"seeds": seeds, "takeovers": open_} if seeds or open_ else None,
    )


def post_load(ctx) -> None:
    params = ctx.params
    checks = []
    with ctx.engine.connect() as connection:
        given = set_counters(ctx, connection)
        ctx.facts["counters_given"] = given
        checks.append(v03_counters(connection, params.target_schema, given))
        orphans = foreign_key_orphans(connection, params.target_schema)
        checks.append(Check("V-04", not orphans, detail=orphans or None))
        filled = empty_tables(connection, params.target_schema, ctx.contract)
        checks.append(Check("empty-tables", not filled, detail=filled or None))
        # The outputs are written before the checks that read them.
        ctx.ledger.write(connection, ctx.outputs)
        checks += [
            v01_accounted(ctx, connection),
            v02_dois(ctx, connection),
            v05_admins(ctx, connection),
            v06_tokens(ctx, connection),
            v07_identities(ctx, connection),
            v09_lineages(ctx, connection),
            v10_votes(ctx, connection),
            v11_copied(ctx, connection),
            v15_accounts(ctx, connection),
        ]
        connection.rollback()
    ctx.checks.extend(checks)
    failed = [c for c in checks if c.blocking and not c.ok]
    if failed:
        raise Refused("E7", [f"{c.name} failed: {c.detail}" for c in failed])
