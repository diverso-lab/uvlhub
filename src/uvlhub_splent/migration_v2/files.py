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
   key names no file, so the rename moves nothing. hubfile's hubfile_alias
   keeps the old folder and name of each, so /hubfiles/raw/<id>/<old name>
   answers a 308 to the new one (hubfile 0.9.0), and the check
   unique-paths holds every path to one file;
5. recovers from Zenodo every file of a published dataset that is
   missing or in mismatch (§6.2 step 5, repair_from_zenodo), with the
   bytes ``zenodo-files`` put in uvlhub_migration_inputs.zenodo_files:
   for a published dataset Zenodo's bytes are what its DOI cites, so they
   win. They go to the file's key as a new file (never through the hard
   link, which would change the mirror), the row takes their size,
   checksum (in the row's algorithm) and sha256, and says ``recovered``;
   when the mirror's bytes are Zenodo's already, the row was the wrong
   part, and only the row changes. The row's old values, and the mirror's
   size and sha256, go to uvlhub_migration.file_repair. What Zenodo cannot
   give stays a conflict, with its dataset, DOI and path, and stops the
   cutover;
6. checks V-08: every file of a published dataset is ok or recovered and
   has its content_sha256, and the bytes in the store are the rows'
   sizes. A draft may miss its files (§6.2 step 6).
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

import sqlalchemy as sa
from splent_io.splent_feature_hubfile.storage import (
    DATASETS,
    TEMPORARY,
    TRASH,
    UPLOADS,
    LocalStorageBackend,
    StorageService,
    checksum_algorithm,
)

from uvlhub_splent.migration_v2.db import insert_batches, qualified, reflect
from uvlhub_splent.migration_v2.ledger import stop_on_conflicts
from uvlhub_splent.migration_v2.params import Refused
from uvlhub_splent.migration_v2.schema import child_env, run_child
from uvlhub_splent.migration_v2.verify import Check

OK, MISSING, MISMATCH, RECOVERED = "ok", "missing", "mismatch", "recovered"
# What a row of a published dataset may say once E8 is done (V-08).
SOUND = (OK, RECOVERED)
# What file_repair says was done.
RESTORED, REPLACED, ROW_FIXED = "restored", "replaced", "row_fixed"
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
    """DM-10: the names E5 planned, and hubfile's aliases with the old ones."""
    target = ctx.params.target_schema
    hubfiles = qualified(target, "hubfiles")
    aliases = reflect(connection, target, only=["hubfile_alias"])["hubfile_alias"]
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
    insert_batches(
        connection,
        aliases,
        [
            {
                "hubfile_id": rename["hubfile_id"],
                "directory_path": rename["directory_path"],
                "name": rename["old_name"],
                "created_at": ctx.params.t0,
            }
            for rename in ctx.renames
        ],
        key="hubfile_id",
    )


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


def checksum_in(algo: str | None, content: bytes) -> tuple[str, str]:
    """(checksum, algorithm) of ``content`` in the row's algorithm: md5 for a
    row of uvlhub before 2.0 (DM-16), sha256 for any other."""
    if algo == "md5":
        return hashlib.md5(content).hexdigest(), "md5"
    return hashlib.sha256(content).hexdigest(), "sha256"


def recovery_inputs(ctx, connection, ids) -> dict[int, dict]:
    """The rows of zenodo_files for ``ids``, without their content."""
    if not ids:
        return {}
    table = ctx.inputs["zenodo_files"]
    columns = [c for c in table.c if c.name != "content"]
    rows = connection.execute(
        sa.select(*columns).where(table.c.hubfile_id.in_(ids))
    ).mappings()
    return {row["hubfile_id"]: dict(row) for row in rows}


def recovered_content(ctx, connection, hubfile_id: int) -> bytes:
    table = ctx.inputs["zenodo_files"]
    return connection.execute(
        sa.select(table.c.content).where(table.c.hubfile_id == hubfile_id)
    ).scalar_one()


def plan_repair(row, given: dict, content: bytes, mirror_sha256) -> dict:
    """What E8 does with a file of a published dataset that Zenodo gave
    back: the row of file_repair, whose ``outcome`` says what changes."""
    checksum, algo = checksum_in(
        row.checksum_algo or checksum_algorithm(row.checksum), content
    )
    sha256 = hashlib.sha256(content).hexdigest()
    if row.storage_status == MISSING:
        outcome = RESTORED
    elif mirror_sha256 == sha256:
        outcome = ROW_FIXED
    else:
        outcome = REPLACED
    return {
        "hubfile_id": row.id,
        "dataset_id": row.dataset_id,
        "deposition_id": given["deposition_id"],
        "outcome": outcome,
        "origin": given["origin"],
        "zenodo_key": given["zenodo_key"],
        "zip_entry": given["zip_entry"],
        "old_status": row.storage_status,
        "old_size": row.size,
        "old_checksum": row.checksum,
        "old_checksum_algo": row.checksum_algo,
        "mirror_size": None,
        "mirror_sha256": mirror_sha256,
        "size": len(content),
        "checksum": checksum,
        "checksum_algo": algo,
        "content_sha256": sha256,
    }


def repair_from_zenodo(ctx, connection, rows, store: Path):
    """§6.2 step 5 on the files of published datasets that are missing or in
    mismatch. Answers why each one that stays so could not be recovered, by
    id, and the ids whose bytes it wrote."""
    target = qualified(ctx.params.target_schema, "hubfiles")
    storage = StorageService(LocalStorageBackend(str(store)))
    wanted = [
        row
        for row in rows
        if row.storage_status in (MISSING, MISMATCH, None)
        and row.dataset_id in ctx.published
    ]
    given = recovery_inputs(ctx, connection, [row.id for row in wanted])
    repairs, unrecovered = [], {}
    for row in wanted:
        entry = given.get(row.id)
        if entry is None:
            unrecovered[row.id] = "zenodo_files has no row for it (run zenodo-files)"
            continue
        if entry["status"] != "ok":
            unrecovered[row.id] = (
                f"Zenodo's record does not give it ({entry['status']})"
            )
            continue
        content = recovered_content(ctx, connection, row.id)
        if (
            entry["dataset_id"] != row.dataset_id
            or len(content) != entry["size"]
            or hashlib.sha256(content).hexdigest() != entry["sha256"]
        ):
            unrecovered[row.id] = "its row of zenodo_files does not hold what it says"
            continue
        mirror_size = mirror_sha256 = None
        if row.storage_status == MISMATCH and row.storage_key:
            path = store / row.storage_key
            mirror_size, mirror_sha256 = path.stat().st_size, row.content_sha256
        repair = plan_repair(row, entry, content, mirror_sha256)
        repair["mirror_size"] = mirror_size
        key = row.storage_key or storage.source_key(row.dataset_id, row.id)
        if repair["outcome"] != ROW_FIXED:
            # A new file renamed over the key: the mirror's, linked there,
            # is never written to.
            with storage.backend.writing(key) as part:
                Path(part).write_bytes(content)
            # What uvl derived from the bytes that were there goes; E9 makes
            # it again from these.
            storage.backend.delete(
                storage.derived_prefix(
                    SimpleNamespace(dataset_id=row.dataset_id, id=row.id)
                )
            )
        if connection.in_transaction():
            connection.commit()
        with connection.begin():
            connection.execute(
                sa.text(
                    f"UPDATE {target} SET storage_key = :key, storage_status = :status, "
                    "size = :size, checksum = :checksum, checksum_algo = :algo, "
                    "content_sha256 = :sha256 WHERE id = :id"
                ),
                {
                    "key": key,
                    "status": RECOVERED,
                    "size": repair["size"],
                    "checksum": repair["checksum"],
                    "algo": repair["checksum_algo"],
                    "sha256": repair["content_sha256"],
                    "id": row.id,
                },
            )
        repairs.append(repair)
    table = ctx.outputs["file_repair"]
    if connection.in_transaction():
        connection.commit()
    with connection.begin():
        connection.execute(table.delete())
    insert_batches(connection, table, repairs, key="hubfile_id")
    outcomes, origins = {}, {}
    for repair in repairs:
        outcomes[repair["outcome"]] = outcomes.get(repair["outcome"], 0) + 1
        origins[repair["origin"]] = origins.get(repair["origin"], 0) + 1
    ctx.facts["zenodo_repair"] = {
        "recovered": len(repairs),
        "by_origin": origins,
        "by_outcome": outcomes,
        "rows_changed": sum(
            1
            for r in repairs
            if (r["size"], r["checksum"]) != (r["old_size"], r["old_checksum"])
        ),
        "not_recovered": sorted(unrecovered),
    }
    written = {r["hubfile_id"] for r in repairs if r["outcome"] != ROW_FIXED}
    return unrecovered, written


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
    select = sa.text(
        "SELECT h.id, h.dataset_id, d.user_id, d.pid, h.name, h.directory_path, "
        "h.checksum, h.size, h.storage_key, h.storage_status, h.checksum_algo, "
        f"h.content_sha256 FROM {qualified(target, 'hubfiles')} h "
        f"JOIN {qualified(target, 'datasets')} d ON d.id = h.dataset_id ORDER BY h.id"
    )
    with ctx.engine.connect() as connection:
        unrecovered, written = repair_from_zenodo(
            ctx, connection, connection.execute(select).all(), store
        )
        connection.commit()
        rows = connection.execute(select).all()
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
        if row.storage_status in SOUND:
            if not row.content_sha256:
                without_digest.append(row.id)
            path = store / row.storage_key
            stored_bytes += path.stat().st_size
            expected_bytes += row.size
            if path.stat().st_nlink < 2 and row.id not in written:
                not_linked.append(row.id)
        elif row.dataset_id in ctx.published:
            unsound.append(row)
            ledger.conflict(
                f"file_{row.storage_status or MISSING}",
                "hubfiles",
                row.id,
                [source[row.id]],
                detail=f"a file of published dataset {row.dataset_id} ({row.pid}), "
                f"{legacy_path(row)}: {unrecovered.get(row.id, 'not recovered')} (§6.2 step 5)",
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
