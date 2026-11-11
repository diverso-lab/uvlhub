"""E2, profiling: the source against a clean v2.12, every anomaly with its
rule, and the decisions people took held to their rows (§3.4, §9.2).

1. P-00. uvlhub_v2_ref is made from v2_12_schema, the monolith's Alembic
   chain to its release, and compared with uvlhub_v2_src both ways: the
   tables (engine, collation), their columns (type, nullability, default,
   collation), their indexes and their foreign keys, these two by what
   they hold and not by their names, which MariaDB gave (A10-15). Each
   difference is a conflict (C-26), but for the ones a rule of the migrator
   reads (drift_rule: a server's default collation, the same bytes), which
   the report lists with their rule; for the rest only a decision that
   accepts it lets the cutover go on.
2. P-01 to P-28 on uvlhub_v2_src: the queries of §9.2, and the ones it
   leaves to Python (P-21, P-23, P-26). Each names the rule of §8 that
   handles what it finds and the stage that applies it. What a probe with
   no rule finds stops E2, rehearsal or not (zero unknowns): a NULL the
   target refuses where the contract has no on_null (P-27b), a publication
   type the target's ENUM does not have (P-17b). uvlhub_migration.profile
   keeps what each found, and the report its count.
3. The decisions of uvlhub_migration_inputs.decision. A decision names its
   conflict (kind and ref) and the source rows it was taken on
   (source_rows and their fingerprint), all copied from
   uvlhub_migration.conflict. E2 reads those rows again: a decision whose
   rows changed or went, of a kind no stage raises, with a resolution the
   migrator does not know (ledger.RESOLUTIONS), or a second one on the same
   conflict stops E2, rehearsal or not. One on a drift is held to the drift
   P-00 finds. The ones that hold close their conflict when its stage
   raises it again; the report lists those no conflict used.

Decisions count only in a run that has E2.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

import sqlalchemy as sa
from splent_io.splent_feature_auth.models import canonical_email

from uvlhub_splent.migration_v2 import contract as contract_module
from uvlhub_splent.migration_v2 import rules, v2_12_schema
from uvlhub_splent.migration_v2.db import (
    all_rows,
    insert_batches,
    qualified,
    quote,
    reflect,
)
from uvlhub_splent.migration_v2.identity import (
    OWN,
    classify_reset_token,
    collation_clashes,
)
from uvlhub_splent.migration_v2.ledger import (
    CONFLICTS,
    RESOLUTIONS,
    SCHEMA,
    fingerprint,
    stop_on_conflicts,
    to_json,
)
from uvlhub_splent.migration_v2.params import Refused

# What uvlhub_migration.profile keeps of what a probe found.
SAMPLE = 20


# ── P-00 ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Drift:
    table: str
    ref: str
    detail: str
    # The information_schema rows of both sides, what its fingerprint is of.
    rows: tuple


_TABLES = """
SELECT table_name AS tbl, engine, table_collation AS coll
FROM information_schema.tables WHERE table_schema = :s AND table_type = 'BASE TABLE'
"""
_COLUMNS = """
SELECT table_name AS tbl, column_name AS col, column_type AS type, is_nullable AS nullable,
       column_default AS dflt, collation_name AS coll, extra
FROM information_schema.columns WHERE table_schema = :s
"""
_INDEXES = """
SELECT table_name AS tbl, non_unique,
       GROUP_CONCAT(column_name ORDER BY seq_in_index) AS cols
FROM information_schema.statistics WHERE table_schema = :s
GROUP BY table_name, index_name, non_unique
"""
_FOREIGN_KEYS = """
SELECT k.table_name AS tbl,
       GROUP_CONCAT(k.column_name ORDER BY k.ordinal_position) AS cols,
       k.referenced_table_name AS parent,
       GROUP_CONCAT(k.referenced_column_name ORDER BY k.ordinal_position) AS parent_cols,
       r.update_rule, r.delete_rule
FROM information_schema.key_column_usage k
JOIN information_schema.referential_constraints r
  ON r.constraint_schema = k.constraint_schema AND r.constraint_name = k.constraint_name
 AND r.table_name = k.table_name
WHERE k.table_schema = :s AND k.referenced_table_name IS NOT NULL
GROUP BY k.table_name, k.constraint_name, k.referenced_table_name, r.update_rule, r.delete_rule
"""


def _read(connection, sql, schema) -> list[dict]:
    return [
        dict(row) for row in connection.execute(sa.text(sql), {"s": schema}).mappings()
    ]


def _side(rows, side):
    return [dict(row, side=side) for row in rows]


def schema_drift(connection, source: str, reference: str) -> list[Drift]:
    """P-00: where ``source`` is not ``reference``, one Drift each, in a
    stable order."""
    found = []
    tables = {
        side: {row["tbl"]: row for row in _read(connection, _TABLES, schema)}
        for side, schema in (("source", source), ("reference", reference))
    }
    common = sorted(set(tables["source"]) & set(tables["reference"]))
    for name in sorted(set(tables["source"]) - set(tables["reference"])):
        found.append(
            Drift(
                name,
                name,
                "a table the clean v2.12 does not have",
                tuple(_side([tables["source"][name]], "source")),
            )
        )
    for name in sorted(set(tables["reference"]) - set(tables["source"])):
        found.append(
            Drift(
                name,
                name,
                "a table of the clean v2.12 the source does not have",
                tuple(_side([tables["reference"][name]], "reference")),
            )
        )
    for name in common:
        here, there = tables["source"][name], tables["reference"][name]
        if (here["engine"], here["coll"]) != (there["engine"], there["coll"]):
            found.append(
                Drift(
                    name,
                    name,
                    f"{here['engine']} {here['coll']}, the clean v2.12 has "
                    f"{there['engine']} {there['coll']}",
                    tuple(_side([here], "source") + _side([there], "reference")),
                )
            )

    columns = {
        side: {
            (row["tbl"], row["col"]): row for row in _read(connection, _COLUMNS, schema)
        }
        for side, schema in (("source", source), ("reference", reference))
    }
    shape = ("type", "nullable", "dflt", "coll", "extra")
    for key in sorted(set(columns["source"]) | set(columns["reference"])):
        if key[0] not in common:
            continue
        here, there = columns["source"].get(key), columns["reference"].get(key)
        if here is not None and there is not None:
            if all(here[f] == there[f] for f in shape):
                continue
            detail = ", ".join(
                f"{f} {here[f]!r} where the clean v2.12 has {there[f]!r}"
                for f in shape
                if here[f] != there[f]
            )
        else:
            detail = (
                "a column the clean v2.12 does not have"
                if there is None
                else "a column of the clean v2.12 the source does not have"
            )
        rows = _side([here] if here else [], "source") + _side(
            [there] if there else [], "reference"
        )
        found.append(Drift(key[0], f"{key[0]}.{key[1]}", detail, tuple(rows)))

    # Indexes and foreign keys by what they hold: their names are MariaDB's.
    for sql, what in ((_INDEXES, "an index"), (_FOREIGN_KEYS, "a foreign key")):
        sides = {}
        for side, schema in (("source", source), ("reference", reference)):
            sides[side] = {}
            for row in _read(connection, sql, schema):
                if row["tbl"] in common:
                    sides[side][tuple(value for _k, value in sorted(row.items()))] = row
        for side, other, detail in (
            ("source", "reference", f"{what} the clean v2.12 does not have"),
            (
                "reference",
                "source",
                f"{what} of the clean v2.12 the source does not have",
            ),
        ):
            for key in sorted(set(sides[side]) - set(sides[other]), key=str):
                row = sides[side][key]
                name = what.split(" ", 1)[1]
                parent = f" -> {row['parent']}" if "parent" in row else ""
                found.append(
                    Drift(
                        row["tbl"],
                        f"{row['tbl']} {name} ({row['cols']}){parent}",
                        detail,
                        tuple(_side([row], side)),
                    )
                )
    return found


# C-26: the drifts a rule of the migrator reads. A table or a column that
# differs from the clean v2.12 in its collation alone, between collations of
# the same character set that a server gives by default (uvlhub.io's
# MariaDB made its tables utf8mb4_general_ci; 11.4, where the clean v2.12 is
# made, gives utf8mb4_uca1400_ai_ci), holds the same bytes. The migrator
# reads them as bytes, compares across schemas in BINARY (§3.4) and gives
# every column of uvlhub3 the contract's collation (DM-15, V-14); the
# accounts are compared in Python and in uvlhub3's collation (P-21), and
# what is compared in the source (DOIs in P-03, cookies in E6) is ASCII,
# which both fold alike. Nothing it loads depends on that collation.
DEFAULT_COLLATIONS = frozenset({"utf8mb4_general_ci", "utf8mb4_uca1400_ai_ci"})
COLLATION_RULE = (
    "C-26: a server's default collation, the same bytes; the migrator reads "
    "them in BINARY and uvlhub3 has the contract's (§3.4, DM-15)"
)


def drift_rule(drift: Drift) -> str | None:
    """The rule that reads ``drift``, or None when none does and it is a
    conflict."""
    sides = {row["side"]: row for row in drift.rows}
    here, there = sides.get("source"), sides.get("reference")
    if here is None or there is None or len(drift.rows) != 2:
        return None
    collations = {here.get("coll"), there.get("coll")}
    if len(collations) != 2 or not collations <= DEFAULT_COLLATIONS:
        return None
    same = set(here) - {"side", "coll"}
    if same != set(there) - {"side", "coll"}:
        return None
    if any(here[key] != there[key] for key in same):
        return None
    return COLLATION_RULE


def build_reference(connection, schema: str) -> None:
    """``schema`` made again from v2_12_schema: the clean v2.12 of P-00."""
    connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {quote(schema)}")
    connection.exec_driver_sql(f"CREATE DATABASE {quote(schema)}")
    connection.exec_driver_sql(f"USE {quote(schema)}")
    for statement in v2_12_schema.statements():
        connection.exec_driver_sql(statement)
    connection.commit()


# ── P-01 to P-28 ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Probe:
    name: str
    title: str
    # The rule of §8 that handles what it finds, and the stage that applies
    # it; None when nothing does, and then what it finds stops E2.
    rule: str | None
    # The query, with {s} for the source schema and :t0 for T0, or a
    # function (ctx, connection) -> rows for what SQL does not say.
    sql: str | None = None
    find: Callable | None = None


def _p17_outside(ctx, connection):
    """P-17b: the publication types the target's ENUM does not have."""
    column = ctx.contract.tables["ds_meta_data"].columns["publication_type"]
    members = set(re.findall(r"'([^']*)'", column.type))
    rows = connection.execute(
        sa.text(
            "SELECT publication_type AS value, COUNT(*) AS n FROM "
            f"{qualified(ctx.params.source_schema, 'ds_meta_data')} "
            "WHERE publication_type IS NOT NULL GROUP BY publication_type"
        )
    ).mappings()
    return [dict(row) for row in rows if row["value"] not in members]


def _p21_canonical(ctx, connection):
    """P-21: addresses one in 3.0, by auth's canonical form and by the
    collation of user.email there."""
    users = connection.execute(
        sa.text(
            f"SELECT id, email FROM {qualified(ctx.params.source_schema, 'user')} "
            "WHERE email IS NOT NULL ORDER BY id"
        )
    ).all()
    groups = defaultdict(list)
    for user_id, email in users:
        groups[canonical_email(email)].append(user_id)
    found = [
        {"how": "canonical", "ids": ids}
        for _canonical, ids in sorted(groups.items(), key=str)
        if len(ids) > 1
    ]
    collation = ctx.contract.tables["user"].columns["email"].collation
    found += [
        {"how": "collation", "ids": ids}
        for ids in collation_clashes(connection, ctx.params.source_schema, collation)
    ]
    return found


def _p23_orcids(ctx, connection):
    """P-23: the ORCID iDs whose check digit (or shape) is wrong."""
    found = []
    for table, column in (("author", "orcid"), ("orcid", "orcid_id")):
        rows = connection.execute(
            sa.text(
                f"SELECT id, {quote(column)} AS orcid FROM "
                f"{qualified(ctx.params.source_schema, table)} "
                f"WHERE {quote(column)} IS NOT NULL AND {quote(column)} <> '' ORDER BY id"
            )
        ).all()
        found += [
            {"table": table, "id": row.id, "orcid": row.orcid}
            for row in rows
            if rules.normalize_orcid(row.orcid) is None
        ]
    return found


def _p26_reset_tokens(ctx, connection):
    """P-26: every reset link that is not one mailed to its account's very
    address, with what it is."""
    user = qualified(ctx.params.source_schema, "user")
    tokens = connection.execute(
        sa.text(
            "SELECT id, token, used_at FROM "
            f"{qualified(ctx.params.source_schema, 'reset_token')} ORDER BY id"
        )
    ).all()
    found = []
    for token in tokens:
        kind, typed, _issued, account = classify_reset_token(
            connection, user, token.token
        )
        if kind != OWN:
            found.append(
                {
                    "id": token.id,
                    "kind": kind,
                    "followed": token.used_at is not None,
                    "account": account.id if account else None,
                }
            )
    return found


def _p27(with_rule: bool):
    def find(ctx, connection):
        """P-27: the NULLs of v2.12 in what a NOT NULL column of 3.0 is
        copied from, read on the source's own schema, which P-00 may find
        nullable where the chain is not."""
        source = contract_module.schema_columns(connection, ctx.params.source_schema)
        found = []
        for table in ctx.contract.by_role(contract_module.LOAD):
            for column in table.columns.values():
                if not column.source or column.nullable:
                    continue
                origin, _, name = column.source.partition(".")
                if not source.get(origin, {}).get(name, {}).get("nullable"):
                    continue
                if bool(column.on_null) != with_rule:
                    continue
                nulls = connection.execute(
                    sa.text(
                        f"SELECT COUNT(*) FROM {qualified(ctx.params.source_schema, origin)} "
                        f"WHERE {quote(name)} IS NULL"
                    )
                ).scalar()
                if nulls:
                    found.append(
                        {
                            "column": f"{table.name}.{column.name}",
                            "source": column.source,
                            "nulls": nulls,
                            "on_null": column.on_null,
                        }
                    )
        return found

    return find


def _p28_objects(ctx, _connection):
    """P-28: what E1 found and dropped before anything read the source."""
    return [{"object": line} for line in ctx.facts.get("p28_objects", [])]


PROBES = (
    Probe(
        "P-01",
        "metadata without a dataset",
        "C-03, DM-4 (E5): with a DOI, a withdrawn dataset whose DOI answers "
        "its tombstone; without one, dropped",
        "SELECT m.id, m.dataset_doi FROM {s}.ds_meta_data m "
        "LEFT JOIN {s}.datasets d ON d.ds_meta_data_id = m.id WHERE d.id IS NULL",
    ),
    Probe(
        "P-02",
        "authors of no dataset",
        "C-04 (E5): dropped, but a tombstone's, which its citation names",
        "SELECT a.id, a.ds_meta_data_id FROM {s}.author a "
        "LEFT JOIN {s}.datasets d ON d.ds_meta_data_id = a.ds_meta_data_id WHERE d.id IS NULL",
    ),
    Probe(
        "P-03",
        "DOIs of more than one metadata",
        "C-10 (E5): a conflict, doi_repeated",
        "SELECT dataset_doi, COUNT(*) AS n FROM {s}.ds_meta_data "
        "WHERE TRIM(dataset_doi) <> '' GROUP BY dataset_doi HAVING n > 1",
    ),
    Probe(
        "P-03b",
        "metadata of more than one dataset",
        "P-03 (E5): a conflict, metadata_shared",
        "SELECT ds_meta_data_id, COUNT(*) AS n FROM {s}.datasets "
        "GROUP BY ds_meta_data_id HAVING n > 1",
    ),
    Probe(
        "P-04",
        "versions without an origin",
        "C-05 (E5): repaired by its concept DOI, else a conflict, lineage_no_origin",
        "SELECT id, dataset_version FROM {s}.datasets "
        "WHERE dataset_version > 1 AND dataset_origin_id IS NULL",
    ),
    Probe(
        "P-04b",
        "origins of more than one version",
        "C-05 (E5): repaired by their concept DOI, else a conflict, lineage_branch",
        "SELECT dataset_origin_id, COUNT(*) AS n FROM {s}.datasets "
        "WHERE dataset_origin_id IS NOT NULL GROUP BY dataset_origin_id HAVING n > 1",
    ),
    Probe(
        "P-04c",
        "versions that do not follow their origin's",
        "C-05 (E5): repaired by its concept DOI, else a conflict, lineage_gap",
        "SELECT c.id, c.dataset_version, p.dataset_version AS origin_version "
        "FROM {s}.datasets c JOIN {s}.datasets p ON p.id = c.dataset_origin_id "
        "WHERE c.dataset_version <> p.dataset_version + 1",
    ),
    Probe(
        "P-05",
        "lineages with more than one concept DOI",
        "C-05 (E5): each concept DOI's datasets one lineage where their "
        "versions rise with their dates (content.repair_lineages); the "
        "lineages of the curation (RU-06) as it made them",
        "WITH RECURSIVE lin AS ("
        " SELECT id, id AS root FROM {s}.datasets WHERE dataset_origin_id IS NULL"
        " UNION ALL"
        " SELECT d.id, lin.root FROM {s}.datasets d JOIN lin ON d.dataset_origin_id = lin.id"
        ") SELECT lin.root, COUNT(DISTINCT m.dataset_concept_doi) AS n "
        "FROM lin JOIN {s}.datasets d ON d.id = lin.id "
        "JOIN {s}.ds_meta_data m ON m.id = d.ds_meta_data_id "
        "WHERE m.dataset_concept_doi IS NOT NULL GROUP BY lin.root HAVING n > 1",
    ),
    Probe(
        "P-06",
        "files whose feature model is in another dataset",
        "C-07 (E5): the file's dataset wins; a conflict when one is published",
        "SELECT h.id, h.dataset_id, f.dataset_id AS model_dataset FROM {s}.hubfiles h "
        "JOIN {s}.feature_model f ON f.id = h.feature_model_id WHERE f.dataset_id <> h.dataset_id",
    ),
    Probe(
        "P-07",
        "paths of more than one file, byte for byte",
        "C-11, DM-10 (E5, E8): ~<id> in the name of every file but the first",
        "SELECT dataset_id, directory_path, name, COUNT(*) AS n FROM {s}.hubfiles "
        "GROUP BY dataset_id, BINARY directory_path, BINARY name HAVING n > 1",
    ),
    Probe(
        "P-08",
        "drafts without a file, a DOI or a deposition",
        "C-08, DM-3 (E5): dropped when older than --ghost-draft-days, "
        "loaded as drafts otherwise",
        "SELECT d.id, d.created_at FROM {s}.datasets d "
        "JOIN {s}.ds_meta_data m ON m.id = d.ds_meta_data_id "
        "LEFT JOIN {s}.hubfiles h ON h.dataset_id = d.id "
        "WHERE h.id IS NULL AND COALESCE(TRIM(m.dataset_doi), '') = '' "
        "AND m.deposition_id IS NULL",
    ),
    Probe(
        "P-09",
        "depositions without a DOI",
        "C-09, A15-04 (E5): published with the DOI Zenodo minted when its "
        "record in zenodo_snapshot validates (a tombstone without its "
        "dataset); failed without one; a conflict when it is another's",
        "SELECT id, deposition_id FROM {s}.ds_meta_data "
        "WHERE deposition_id IS NOT NULL AND COALESCE(TRIM(dataset_doi), '') = ''",
    ),
    Probe(
        "P-09b",
        "DOIs whose metadata Zenodo does not have yet",
        "C-09 (E5): sync_pending, held as DM-9 says",
        "SELECT id, dataset_doi FROM {s}.ds_meta_data "
        "WHERE TRIM(dataset_doi) <> '' AND metadata_synced = 0",
    ),
    Probe(
        "P-10",
        "pending transfer offers",
        "C-18, D13 b (E5): cancelled at T0",
        "SELECT id, dataset_id, from_user_id, to_user_id, created_at "
        "FROM {s}.dataset_transfer_request WHERE status = 'PENDING'",
    ),
    Probe(
        "P-11",
        "ORCID rows of no profile, or apart from external_identity",
        "C-14 (E4): folded into external_identity, or a conflict",
        "SELECT o.id, o.orcid_id, p.user_id, e.user_id AS identity_user "
        "FROM {s}.orcid o LEFT JOIN {s}.user_profile p ON p.id = o.profile_id "
        "LEFT JOIN {s}.external_identity e ON e.provider = 'orcid' "
        " AND BINARY e.provider_id = BINARY o.orcid_id "
        "WHERE p.id IS NULL OR e.id IS NULL OR e.user_id <> p.user_id",
    ),
    Probe(
        "P-11b",
        "GitHub rows apart from external_identity",
        "C-14 (E4): folded into external_identity, or a conflict",
        "SELECT g.id, g.github_id, p.user_id, e.user_id AS identity_user "
        "FROM {s}.github g LEFT JOIN {s}.user_profile p ON p.id = g.profile_id "
        "LEFT JOIN {s}.external_identity e ON e.provider = 'github' "
        " AND BINARY e.provider_id = BINARY CAST(g.github_id AS CHAR) "
        "WHERE p.id IS NULL OR e.id IS NULL OR e.user_id <> p.user_id",
    ),
    Probe(
        "P-11c",
        "accounts with two identities of one provider",
        "C-14 (E4): a conflict, identity_second_link",
        "SELECT user_id, provider, COUNT(*) AS n FROM {s}.external_identity "
        "GROUP BY user_id, provider HAVING n > 1",
    ),
    Probe(
        "P-12",
        "votes on a version that is not the first",
        "C-06, DM-8 (E5): moved to the root, the latest of a user's wins",
        "SELECT r.id, r.dataset_id FROM {s}.dataset_rating r "
        "JOIN {s}.datasets d ON d.id = r.dataset_id WHERE d.dataset_origin_id IS NOT NULL",
    ),
    Probe(
        "P-12b",
        "votes on one's own dataset",
        "C-06, DM-8 (E5): dropped",
        "SELECT r.id, r.dataset_id FROM {s}.dataset_rating r "
        "JOIN {s}.datasets d ON d.id = r.dataset_id WHERE r.user_id = d.user_id",
    ),
    Probe(
        "P-13",
        "API keys D12 carries over revoked or dates by a rule",
        "D12 (E4): no scopes, never used or unused for a year: revoked; "
        "no date: last_used_at, else T0",
        "SELECT id, scopes, created_at IS NULL AS undated, last_used_at IS NULL AS never_used "
        "FROM {s}.api_keys WHERE scopes = '' OR created_at IS NULL OR last_used_at IS NULL "
        "OR last_used_at < :t0 - INTERVAL 365 DAY",
    ),
    Probe(
        "P-14",
        "datasets whose feature_model_count is wrong",
        "C-12 (E5): counted again",
        "SELECT d.id, d.feature_model_count, COUNT(f.id) AS counted "
        "FROM {s}.datasets d LEFT JOIN {s}.feature_model f ON f.dataset_id = d.id "
        "GROUP BY d.id, d.feature_model_count HAVING d.feature_model_count <> COUNT(f.id)",
    ),
    Probe(
        "P-15",
        "files without a FactLabel",
        "C-21 (E9, DM-6): every FactLabel is computed again",
        "SELECT h.id FROM {s}.hubfiles h LEFT JOIN {s}.hubfile_factlabel f "
        "ON f.hubfile_id = h.id WHERE f.factlabel_json IS NULL",
    ),
    Probe(
        "P-16",
        "accounts without a profile",
        "§5.1 (E4): loaded; profile makes one when it is needed",
        "SELECT u.id FROM {s}.`user` u LEFT JOIN {s}.user_profile p ON p.user_id = u.id "
        "WHERE p.id IS NULL",
    ),
    Probe(
        "P-16b",
        "accounts without an address, or switched off",
        "§5.1 (E4): the address stays NULL; disabled_at is T0",
        "SELECT id, email IS NULL AS no_email, active = 0 AS inactive FROM {s}.`user` "
        "WHERE email IS NULL OR active = 0",
    ),
    Probe(
        "P-16c",
        "password hashes by method",
        "§5.2 (E4): copied as they are",
        "SELECT SUBSTRING_INDEX(password, '$', 1) AS method, COUNT(*) AS n "
        "FROM {s}.`user` GROUP BY method",
    ),
    Probe(
        "P-17",
        "publication types",
        "C-17 (E5): copied as they are, the ENUM's member names",
        "SELECT publication_type, COUNT(*) AS n FROM {s}.ds_meta_data GROUP BY publication_type",
    ),
    Probe(
        "P-17b",
        "publication types the target's ENUM does not have",
        None,
        find=_p17_outside,
    ),
    Probe(
        "P-18",
        "rows of statistics",
        "C-19 (E5): its counters are in the report",
        "SELECT * FROM {s}.statistics",
    ),
    Probe(
        "P-18b",
        "DOI mappings",
        "C-20 (E6): each chain followed to its end, into doi_mapping and "
        "legacy_url; a cycle or a dead end is a conflict",
        "SELECT * FROM {s}.doi_mapping",
    ),
    Probe(
        "P-19",
        "the Alembic head",
        "E1: MIGRATION_EXPECTED_HEAD",
        "SELECT version_num FROM {s}.alembic_version",
    ),
    Probe(
        "P-20",
        "tables by size",
        "§9.4: the window's budget",
        "SELECT table_name, table_rows, data_length + index_length AS bytes, "
        "auto_increment, table_collation FROM information_schema.tables "
        "WHERE table_schema = :schema ORDER BY bytes DESC",
    ),
    Probe(
        "P-21",
        "addresses that are one in 3.0",
        "C-13 (E4): the accounts are held, a conflict",
        find=_p21_canonical,
    ),
    Probe(
        "P-22",
        "descriptions with markup",
        "C-01, C-29 (E5): cleaned again as html_legacy, the originals in "
        "quarantine_description (B0's after the hotfix D1); the report counts "
        "each element and the active content (content.describe)",
        "SELECT id FROM {s}.ds_meta_data WHERE description LIKE '%<%'",
    ),
    Probe(
        "P-23",
        "ORCID iDs that are not valid",
        "C-15 (E5): an author's is NULL; C-14 (E4): an identity's is a conflict",
        find=_p23_orcids,
    ),
    Probe(
        "P-24",
        "checksums by algorithm",
        "C-24 (E5, E8): checked with md5 or sha256 as the row's is",
        "SELECT CASE WHEN h.checksum REGEXP '^[0-9a-fA-F]{{64}}$' THEN 'sha256' "
        "WHEN h.checksum REGEXP '^[0-9a-fA-F]{{32}}$' THEN 'md5' ELSE 'other' END AS algo, "
        "COUNT(*) AS n, MIN(d.created_at) AS since, MAX(d.created_at) AS until "
        "FROM {s}.hubfiles h JOIN {s}.datasets d ON d.id = h.dataset_id GROUP BY algo",
    ),
    Probe(
        "P-25",
        "accounts of the development seed",
        "C-25 (E4): dropped, with what is theirs",
        "SELECT id, email FROM {s}.`user` WHERE email LIKE '%@example.com'",
    ),
    Probe(
        "P-25b",
        "DOIs that are not Zenodo's, or not their deposition's",
        "C-30 (E5): a conflict, doi_not_zenodo or doi_not_its_deposition; "
        "one whose record does not validate is doi_record_missing",
        "SELECT id, dataset_doi, deposition_id FROM {s}.ds_meta_data "
        "WHERE TRIM(dataset_doi) <> '' AND (dataset_doi NOT LIKE '10.5281/zenodo.%' "
        "OR deposition_id IS NULL OR dataset_doi <> CONCAT('10.5281/zenodo.', deposition_id))",
    ),
    Probe(
        "P-25c",
        "checksums of no algorithm",
        "C-25 (E5): a conflict, checksum_unknown",
        "SELECT id, checksum FROM {s}.hubfiles "
        "WHERE checksum NOT REGEXP '^([0-9a-fA-F]{{32}}|[0-9a-fA-F]{{64}})$'",
    ),
    Probe(
        "P-26",
        "reset links not mailed to their account's very address",
        "C-28, §5.1 (E4): another spelling followed is a probable takeover, "
        "not followed an attempt; the rest proves nothing",
        find=_p26_reset_tokens,
    ),
    Probe(
        "P-27",
        "NULLs the target refuses, with a rule",
        "C-27: the contract's on_null",
        find=_p27(with_rule=True),
    ),
    Probe(
        "P-27b",
        "NULLs the target refuses, without a rule",
        None,
        find=_p27(with_rule=False),
    ),
    Probe(
        "P-28",
        "triggers, routines, events and views",
        "E1: listed and dropped from the source",
        find=_p28_objects,
    ),
)


def run_probes(ctx, connection) -> list[tuple[Probe, list[dict]]]:
    params = ctx.params
    found = []
    for probe in PROBES:
        if probe.find is not None:
            rows = probe.find(ctx, connection)
        else:
            sql = probe.sql.format(s=quote(params.source_schema))
            rows = [
                dict(row)
                for row in connection.execute(
                    sa.text(sql), {"t0": params.t0, "schema": params.source_schema}
                ).mappings()
            ]
        found.append((probe, rows))
    return found


# ── Decisions ────────────────────────────────────────────────────────────


def read_decisions(ctx, connection) -> list[dict]:
    """Every decision of the inputs schema, in id order. One made before
    decisions named their rows cannot be held to them, and stops E2."""
    params = ctx.params
    have = set(
        connection.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = :s AND table_name = 'decision'"
            ),
            {"s": params.inputs_schema},
        ).scalars()
    )
    lacking = sorted(set(ctx.inputs["decision"].c.keys()) - have)
    if lacking:
        raise Refused(
            "E2",
            f"{params.inputs_schema}.decision has no {', '.join(lacking)}: it "
            "predates decisions that name their rows; add the column, and copy "
            "it from uvlhub_migration.conflict",
        )
    return all_rows(connection, ctx.inputs["decision"])


def read_sources(connection, schema: str, refs) -> dict[str, list[dict]]:
    """The rows "table:id" of ``refs`` in ``schema``, whole, by table, as a
    stage reads them (all_rows): what a fingerprint is of."""
    ids = defaultdict(list)
    for ref in refs:
        table, _, row_id = ref.rpartition(":")
        ids[table].append(int(row_id))
    tables = reflect(connection, schema, only=sorted(ids)) if ids else {}
    found = {}
    for name, wanted in sorted(ids.items()):
        table = tables[name]
        rows = connection.execute(
            sa.select(table).where(table.c.id.in_(wanted)).order_by(table.c.id)
        ).mappings()
        found[name] = [dict(row) for row in rows]
    return found


def check_decisions(ctx, connection, decisions) -> list[str]:
    """Why the decisions that do not hold do not, one line each. The ones
    that hold go to the ledger, which closes their conflicts."""
    problems, holding = [], {}
    for decision in decisions:
        where = f"decision {decision['id']} ({decision['kind']} {decision['ref']})"
        key = (decision["kind"], decision["ref"])
        if decision["kind"] not in CONFLICTS:
            problems.append(f"{where}: no stage raises a conflict of that kind")
            continue
        if decision["resolution"] not in RESOLUTIONS:
            problems.append(
                f"{where}: resolution {decision['resolution']!r} is none of "
                f"{', '.join(RESOLUTIONS)}"
            )
            continue
        if key in holding:
            problems.append(
                f"{where}: decision {holding[key]['id']} decides the same conflict"
            )
            continue
        if decision["kind"] != "schema_drift":
            # The drifts are held to what P-00 finds, which raises them.
            try:
                refs = json.loads(decision["source_rows"] or "[]")
                sources = read_sources(connection, ctx.params.source_schema, refs)
            except (ValueError, KeyError, sa.exc.SQLAlchemyError):
                problems.append(f"{where}: its source_rows name no rows of the source")
                continue
            if fingerprint(sources) != decision["fingerprint"]:
                problems.append(
                    f"{where}: the rows it was taken on ({', '.join(refs)}) "
                    "changed, or are not there any more"
                )
                continue
        holding[key] = decision
    ctx.ledger.decisions = holding
    return problems


def profile(ctx) -> None:
    params, ledger = ctx.params, ctx.ledger
    with ctx.engine.connect() as connection:
        decisions = read_decisions(ctx, connection)
        problems = check_decisions(ctx, connection, decisions)
        connection.rollback()

    with ctx.engine.connect() as connection:
        build_reference(connection, params.reference_schema)
    with ctx.engine.connect() as connection:
        drifts = schema_drift(connection, params.source_schema, params.reference_schema)
        ruled = []
        for drift in drifts:
            rule = drift_rule(drift)
            if rule is not None:
                ruled.append({"ref": drift.ref, "detail": drift.detail, "rule": rule})
                continue
            ledger.conflict(
                "schema_drift",
                drift.table,
                drift.ref,
                {SCHEMA: list(drift.rows)},
                detail=drift.detail,
            )
        found = run_probes(ctx, connection)
        connection.rollback()

    raised = {(c["kind"], c["ref"]) for c in ledger.conflicts} | {
        ("schema_drift", r["ref"]) for r in ruled
    }
    for (kind, ref), decision in sorted(ledger.decisions.items()):
        if kind == "schema_drift" and (kind, ref) not in raised:
            problems.append(
                f"decision {decision['id']} ({kind} {ref}): P-00 finds that drift "
                "no more"
            )
    problems += ledger.stale
    ledger.stale = []

    table = ctx.outputs["profile"]
    rows = [
        {
            "name": probe.name,
            "title": probe.title,
            "rule": probe.rule,
            "found": len(rows),
            "detail": to_json(rows[:SAMPLE]) if rows else None,
        }
        for probe, rows in found
    ]
    with ctx.engine.connect() as connection:
        insert_batches(connection, table, rows, key="name")
    ctx.facts["profile"] = {row["name"]: row["found"] for row in rows}
    ctx.facts["schema_drift"] = len(drifts)
    # What P-00 found that a rule reads, with the rule; the rest is open.
    ctx.facts["schema_drift_ruled"] = ruled

    unruled = [
        f"{probe.name} {probe.title}: {len(rows)} found, and no rule of the "
        f"migrator handles them ({to_json(rows[:3])})"
        for probe, rows in found
        if probe.rule is None and rows
    ]
    if problems or unruled:
        raise Refused("E2", problems + unruled)
    stop_on_conflicts(ctx, "E2")
