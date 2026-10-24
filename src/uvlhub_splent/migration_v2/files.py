"""E8, files: v2.12's uploads/ into hubfile's store by key (§6, MIG-05).

The operator mirrors v2.12's uploads/ into ``<store>/.legacy_mirror/``
(rsync -a --delete, never --inplace), inside the same mount as the store,
so a file is hard linked to its key instead of copied: link(2) answers
EXDEV across mounts, even within one file system (R-27). E8 then:

1. empties the store but for the mirror (principle 3: every run links again);
2. runs hubfile's own ``storage-migrate --source <mirror> --link``, in a
   process of its own (it is the feature's command, and it writes through
   the ORM): each file is checked against its row, its size and its
   checksum with the row's algorithm, md5 before uvlhub 2.0 (C-24), linked
   to ``datasets/<id>/src/<hubfile_id>``, and its row says what was found
   (storage_status ok, mismatch, unverified, missing or conflict) with the
   sha256 of the content;
3. writes file_manifest from what the rows say, plus every file of the
   mirror no row accounts for (orphan, temp, derived);
4. writes the names DM-10 gives a second file on one path (E5's
   plan_renames): storage-migrate found each file by its v2.12 name, and a
   key names no file, so the rename moves nothing. file_alias keeps the
   old names, and the check unique-paths holds every path to one file;
5. checks V-08: every file of a published dataset is ok and has its
   content_sha256, and the bytes in the store are the rows' sizes. A
   published file missing or in mismatch is recovered from Zenodo (§6.2
   step 5, zenodo_files), which this pass does not do: it is a conflict,
   and stops the cutover. A draft may miss its files (§6.2 step 6).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import sqlalchemy as sa
from splent_io.splent_feature_hubfile.storage import DATASETS, TEMPORARY, TRASH, UPLOADS

from uvlhub_splent.migration_v2.db import insert_batches, qualified, reflect
from uvlhub_splent.migration_v2.ledger import stop_on_conflicts
from uvlhub_splent.migration_v2.params import Refused
from uvlhub_splent.migration_v2.schema import child_env, run_child
from uvlhub_splent.migration_v2.verify import Check

OK, MISSING = "ok", "missing"
# The folders of v2.12's uploads/ that are no file of a dataset (§2.2):
# the staging of uploads under way, and what flamapy derived, which 3.0
# makes again (UV-4).
TEMP_FOLDER = "temp"
DERIVED_FOLDERS = ("glencoe", "dimacs", "splot")


def legacy_path(row) -> str:
    """Where v2.12 kept the file: user_<owner>/dataset_<id>/uvl/<dir>/<name>."""
    parts = [f"user_{row.user_id}", f"dataset_{row.dataset_id}", "uvl"]
    if row.directory_path:
        parts += row.directory_path.split("/")
    parts.append(row.name)
    return "/".join(parts)


# What hubfile keeps at the top of its store. Emptying the store removes
# these and nothing else.
STORE_FOLDERS = (DATASETS, UPLOADS, TEMPORARY, TRASH)


def empty_store(store: Path, mirror: Path) -> None:
    """Remove what hubfile keeps in ``store``, the mirror aside (principle 3:
    every run links again). Anything else there means ``store`` is not
    hubfile's store (v2.12's uploads/, a volume's root), and nothing is
    removed."""
    stray = sorted(
        entry.name
        for entry in store.iterdir()
        if entry != mirror and entry.name not in STORE_FOLDERS
    )
    if stray:
        raise Refused(
            "E8",
            f"{store} holds {', '.join(stray)}, which hubfile's store does not: "
            "it is not the store, and nothing was removed",
        )
    for name in STORE_FOLDERS:
        entry = store / name
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        elif entry.exists() or entry.is_symlink():
            entry.unlink()


def mirror_files(mirror: Path):
    for folder, _dirs, names in os.walk(mirror):
        for name in names:
            yield Path(folder, name).relative_to(mirror).as_posix()


def classify(path: str) -> str:
    """What a file of the mirror no row names is (§6.2 step 1)."""
    parts = path.split("/")
    if parts[0] == TEMP_FOLDER:
        return "temp"
    if len(parts) > 2 and parts[0].startswith("user_") and parts[2] in DERIVED_FOLDERS:
        return "derived"
    return "orphan"


def rename_duplicates(ctx, connection) -> None:
    """DM-10: the names E5 planned, and file_alias with the old ones."""
    hubfiles = qualified(ctx.params.target_schema, "hubfiles")
    if connection.in_transaction():
        connection.commit()
    with connection.begin():
        for rename in ctx.renames:
            connection.execute(
                sa.text(
                    f"UPDATE {hubfiles} SET name = :new_name "
                    "WHERE id = :hubfile_id AND BINARY name = BINARY :old_name"
                ),
                rename,
            )
    insert_batches(connection, ctx.outputs["file_alias"], ctx.renames, key="hubfile_id")


def shared_paths(connection, schema) -> list[str]:
    """The paths of uvlhub3 more than one file of a dataset has, compared
    byte for byte, as hubfile resolves a file by its relative_path."""
    rows = connection.execute(
        sa.text(
            "SELECT dataset_id, directory_path, name, COUNT(*) AS n "
            f"FROM {qualified(schema, 'hubfiles')} "
            "GROUP BY dataset_id, BINARY directory_path, BINARY name HAVING n > 1"
        )
    ).all()
    return [f"{r.dataset_id}:{r.directory_path}/{r.name} ({r.n})" for r in rows]


def source_rows(ctx, ids) -> dict[int, dict]:
    """The rows of v2.12's hubfiles with ``ids``, whole: what a conflict
    about a file is about."""
    if not ids:
        return {}
    with ctx.engine.connect() as connection:
        table = reflect(connection, ctx.params.source_schema, only=["hubfiles"])[
            "hubfiles"
        ]
        found = connection.execute(
            sa.select(table).where(table.c.id.in_(ids)).order_by(table.c.id)
        ).mappings()
        return {row["id"]: dict(row) for row in found}


def files(ctx) -> None:
    params, ledger = ctx.params, ctx.ledger
    store, mirror = params.store_root, params.mirror
    if store is None or mirror is None or not mirror.is_dir():
        raise Refused("E8", f"no mirror of v2.12's uploads/ at {mirror}")
    if store.stat().st_dev != mirror.stat().st_dev:
        raise Refused(
            "E8",
            f"{mirror} is on another device than {store}: no hard link can join them (R-27)",
        )
    empty_store(store, mirror)

    command = list(params.files_command) + ["--source", str(mirror), "--link"]
    output = run_child(
        "E8", command, child_env(params, HUBFILE_STORAGE_ROOT=str(store))
    )
    ctx.facts["storage_migrate_output"] = output.strip().splitlines()[-20:]

    target = params.target_schema
    with ctx.engine.connect() as connection:
        rows = connection.execute(
            sa.text(
                "SELECT h.id, h.dataset_id, d.user_id, h.name, h.directory_path, h.checksum, "
                "h.size, h.storage_key, h.storage_status, h.checksum_algo, h.content_sha256 "
                f"FROM {qualified(target, 'hubfiles')} h "
                f"JOIN {qualified(target, 'datasets')} d ON d.id = h.dataset_id ORDER BY h.id"
            )
        ).all()
        manifest, accounted = [], set()
        for row in rows:
            path = legacy_path(row)
            accounted.add(path)
            manifest.append(
                {
                    "hubfile_id": row.id,
                    "dataset_id": row.dataset_id,
                    "path": path,
                    "storage_key": row.storage_key,
                    "checksum_algo": row.checksum_algo,
                    "checksum": row.checksum,
                    "content_sha256": row.content_sha256,
                    "size": row.size,
                    "status": row.storage_status or MISSING,
                }
            )
        for path in sorted(set(mirror_files(mirror)) - accounted):
            manifest.append(
                {
                    "hubfile_id": None,
                    "dataset_id": None,
                    "path": path,
                    "storage_key": None,
                    "checksum_algo": None,
                    "checksum": None,
                    "content_sha256": None,
                    "size": (mirror / path).stat().st_size,
                    "status": classify(path),
                }
            )
        numbered = [dict(entry, id=i) for i, entry in enumerate(manifest, 1)]
        table = ctx.outputs["file_manifest"]
        connection.commit()
        with connection.begin():
            connection.execute(table.delete())
        insert_batches(connection, table, numbered)
        rename_duplicates(ctx, connection)
        shared = shared_paths(connection, target)
    ctx.checks.append(Check("unique-paths", not shared, detail=shared or None))

    by_status = {}
    for entry in manifest:
        by_status[entry["status"]] = by_status.get(entry["status"], 0) + 1
    ctx.facts["files"] = by_status

    unsound, without_digest, not_linked = [], [], []
    stored_bytes = expected_bytes = 0
    source = source_rows(
        ctx,
        [
            row.id
            for row in rows
            if row.storage_status != OK and row.dataset_id in ctx.published
        ],
    )
    for row in rows:
        if row.storage_status == OK:
            if not row.content_sha256:
                without_digest.append(row.id)
            path = store / row.storage_key
            stored_bytes += path.stat().st_size
            expected_bytes += row.size
            if path.stat().st_nlink < 2:
                not_linked.append(row.id)
        elif row.dataset_id in ctx.published:
            unsound.append(row)
            ledger.conflict(
                f"file_{row.storage_status or MISSING}",
                "hubfiles",
                row.id,
                [source[row.id]],
                detail=f"a file of published dataset {row.dataset_id}: recover it from Zenodo (§6.2 step 5)",
            )
    ctx.checks.append(
        Check(
            "V-08",
            not unsound and not without_digest and stored_bytes == expected_bytes,
            detail={
                "by_status": by_status,
                "published_not_ok": [r.id for r in unsound],
                "ok_without_sha256": without_digest,
                "bytes": {"stored": stored_bytes, "rows": expected_bytes},
                "not_hard_linked": not_linked,
            },
        )
    )
    with ctx.engine.connect() as connection:
        ctx.ledger.write(connection, ctx.outputs)
    stop_on_conflicts(ctx, "E8")
    if without_digest or stored_bytes != expected_bytes:
        raise Refused("E8", [f"V-08 failed: {ctx.checks[-1].detail}"])
    if shared and not ctx.params.allow_open_conflicts:
        raise Refused("E8", [f"unique-paths failed: {', '.join(shared)}"])
