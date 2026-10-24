"""E5, content: datasets and everything hanging off them (§2.1, §4.3, §8).

FIRST PASS. It loads ds_metrics, ds_meta_data, datasets, author,
feature_model, hubfiles, hubfile_metrics, dataset_rating and
dataset_transfer_request into the tables of dataset 0.5.0, hubfile 0.5.0,
featuremodel 0.4.0 (the uvl feature keeps the table), factlabel 0.4.0 and
rating 0.3.0, ids kept, with the rules the pinned features apply to rows
that predate them. What the final E5 still has to do is in DEFERRED, and
the report repeats it: a run that went through this pass is never ready
for the cutover.

What it applies already:

- status and visibility by dataset's own state_from_metadata (DL-1);
  published_at is created_at, as dataset0002 sets it;
- the identifier as dataset0005 makes it neutral: a DOI is the pid, with
  the scheme doi, and a dataset with a DOI or a deposition is zenodo's;
- the authors of an anonymous dataset in private_authors, as dataset0003
  moves them (DS-3); an author's ORCID normalised, NULL when invalid (C-15);
- the seed's datasets (P-25), ghost drafts (DM-3), orphan metadata (P-01:
  a tombstone when it has a DOI, dropped otherwise) and orphan authors
  (P-02) are not loaded, each with its reason;
- a feature model follows its file's dataset (C-07); checksum_algo and
  artifact_type as hubfile0002 reads them (P-24); feature_model_count is
  counted again (C-12);
- votes move to the root of their lineage, the latest of a user's wins and
  self-votes go (DM-8, C-06); pending transfers are cancelled at T0 (D13 b).

What it finds and leaves open, as conflicts: DOIs that are not Zenodo's
production (C-30), DOIs or metadata shared by two datasets (C-10, P-03),
lineages with a missing origin, branches or gaps (C-05), two rows on one
path (C-11), checksums of no known algorithm (C-25), and a file whose
feature model is in another, published dataset (C-07).
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import timedelta

from splent_io.splent_feature_dataset.models import (
    DOI_SCHEME,
    LEGACY_PROVIDER,
    DatasetStatus,
    state_from_metadata,
)
from splent_io.splent_feature_hubfile.storage import checksum_algorithm

from uvlhub_splent.migration_v2 import rules
from uvlhub_splent.migration_v2.db import (
    all_rows,
    foreign_keys_off,
    insert_batches,
    reflect,
)
from uvlhub_splent.migration_v2.ledger import stop_on_conflicts, to_json

FIRST_PASS = True

DEFERRED = (
    "C-01, C-29: descriptions are copied as they are, which dataset renders "
    "through rich_text; re-sanitising them, the originals in "
    "quarantine_description from B0, waits for DS-1 (description_format)",
    "C-05: lineages load as they are and their faults are listed; repairing "
    "them by concept DOI waits for the Zenodo snapshot (MIG-06)",
    "§4.3: published_at is created_at, and a deposition without a DOI is "
    "failed; Zenodo's date and its published records (A15-04) wait for the "
    "snapshot",
    "C-10, C-11, C-30: found and left open, for the decisions (DM-10)",
    "C-16, C-23: publication_doi and tags are copied as they are (DS-1 and "
    "dataset_tag do not exist in the pinned features)",
    "CO-5, D14, DL-5, DL-6: public_id, concept_pid, lineage_root_id, "
    "author.position and author.user_id have no column yet",
    "§7.3: hubfile_metrics is copied without status = 'legacy', which "
    "factlabel has no column for",
    "§5.7: the offers it cancels carry no reason (no column); the report lists them",
)

SOURCE_TABLES = (
    "ds_metrics",
    "ds_meta_data",
    "datasets",
    "author",
    "feature_model",
    "hubfiles",
    "hubfile_metrics",
    "hubfile_factlabel",
    "dataset_rating",
    "dataset_transfer_request",
    "doi_mapping",
    "statistics",
    "ds_view_record",
    "ds_download_record",
    "hubfile_view_record",
    "hubfile_download_record",
)
TARGET_TABLES = (
    "ds_metrics",
    "ds_meta_data",
    "datasets",
    "author",
    "feature_model",
    "hubfiles",
    "hubfile_metrics",
    "dataset_rating",
    "dataset_transfer_request",
)
# What E6 and E9 fill or rebuild, counted here so the report says it.
LATER = {
    "hubfile_factlabel": "E9: recomputed (DM-6)",
    "doi_mapping": "E6: aliases in legacy_url (C-20)",
    "statistics": "dropped (DC-7): its counters are in the report",
    "ds_view_record": "E6: daily aggregates (DM-5)",
    "ds_download_record": "E6: daily aggregates (DM-5)",
    "hubfile_view_record": "E6: daily aggregates (DM-5)",
    "hubfile_download_record": "E6: daily aggregates (DM-5)",
}
PUBLISHED = (DatasetStatus.PUBLISHED.value, DatasetStatus.SYNC_PENDING.value)


def _doi(meta) -> str | None:
    return (meta["dataset_doi"] or "").strip() or None


def choose_datasets(ctx, datasets, metas, files_of) -> dict[int, dict]:
    """The datasets that load, by id; the others dropped with their reason."""
    params, ledger = ctx.params, ctx.ledger
    loaded_users = ctx.loaded["user"]
    ghost_before = params.t0 - timedelta(days=params.ghost_draft_days)
    chosen = {}
    for dataset in datasets:
        meta = metas[dataset["ds_meta_data_id"]]
        if dataset["user_id"] not in loaded_users:
            ledger.drop(
                "datasets", dataset["id"], ledger.owner_reason(dataset["user_id"])
            )
            continue
        if (
            _doi(meta) is None
            and meta["deposition_id"] is None
            and not files_of[dataset["id"]]
            and dataset["created_at"] < ghost_before
        ):
            ledger.drop(
                "datasets",
                dataset["id"],
                "ghost_draft",
                f"DM-3: {params.ghost_draft_days} days",
            )
            continue
        chosen[dataset["id"]] = dataset
    return chosen


def check_lineages(ctx, datasets, chosen) -> dict[int, int | None]:
    """C-05 (P-04): the origin of every loaded dataset, None where it is not
    loaded, and a conflict for every fault of a lineage."""
    ledger = ctx.ledger
    by_id = {dataset["id"]: dataset for dataset in datasets}
    origins = {}
    children = defaultdict(list)
    for dataset in chosen.values():
        origin = dataset["dataset_origin_id"]
        if origin is not None and origin not in chosen:
            ledger.conflict(
                "lineage_origin_not_loaded",
                "datasets",
                dataset["id"],
                [dataset, by_id.get(origin) or {"id": origin}],
                detail=f"its origin {origin} is not loaded; it loads as an original",
            )
            origin = None
        origins[dataset["id"]] = origin
        if origin is not None:
            children[origin].append(dataset)
        elif (dataset["dataset_version"] or 1) > 1:
            ledger.conflict(
                "lineage_no_origin",
                "datasets",
                dataset["id"],
                [dataset],
                detail=f"version {dataset['dataset_version']} with no origin",
            )
    for origin, group in sorted(children.items()):
        if len(group) > 1:
            ledger.conflict(
                "lineage_branch",
                "datasets",
                origin,
                group,
                detail=f"{len(group)} datasets claim {origin} as their origin",
            )
        for child in group:
            expected = (chosen[origin]["dataset_version"] or 1) + 1
            if (child["dataset_version"] or 1) != expected:
                ledger.conflict(
                    "lineage_gap",
                    "datasets",
                    child["id"],
                    [child, chosen[origin]],
                    detail=f"version {child['dataset_version']} after {expected - 1}",
                )
    return origins


def build_metadata(ctx, metas, datasets_of_meta, chosen, authors_of):
    """ds_meta_data rows of the loaded datasets; orphans to tombstones or
    dropped (P-01); DOIs checked (C-10, C-30)."""
    ledger = ctx.ledger
    loaded_users = ctx.loaded["user"]
    rows = []
    owners_of_doi = defaultdict(list)
    for meta in metas.values():
        datasets = datasets_of_meta[meta["id"]]
        loading = [d for d in datasets if d["id"] in chosen]
        if not datasets:
            if _doi(meta) is not None:
                ledger.tombstones.append(
                    {
                        "doi": _doi(meta),
                        "ds_meta_data_id": meta["id"],
                        "snapshot": to_json(meta),
                    }
                )
                ledger.drop("ds_meta_data", meta["id"], "tombstone", _doi(meta))
            else:
                ledger.drop("ds_meta_data", meta["id"], "orphan")
            continue
        if not loading:
            reason = ledger.reason("datasets", datasets[0]["id"], "dataset_not_loaded")
            ledger.drop(
                "ds_meta_data", meta["id"], reason, f"dataset {datasets[0]['id']}"
            )
            continue
        if len(datasets) > 1:
            ledger.conflict(
                "metadata_shared",
                "ds_meta_data",
                meta["id"],
                [meta, *datasets],
                detail=f"datasets {', '.join(str(d['id']) for d in datasets)} share it",
            )
        doi = _doi(meta)
        if doi is not None:
            owners_of_doi[doi].append(meta)
            if not rules.doi_is_zenodo(doi):
                ledger.conflict(
                    "doi_not_zenodo",
                    "ds_meta_data",
                    doi,
                    [meta],
                    detail="not a DOI of Zenodo's production (10.5281)",
                )
        publisher = meta["api_publisher_user_id"]
        if publisher is not None and publisher not in loaded_users:
            ledger.note(
                "ds_meta_data: api_publisher_user_id of an account not loaded, NULL"
            )
            publisher = None
        anonymous = meta["dataset_anonymous"] == 1
        concealed = None
        if anonymous:
            concealed = [
                {
                    "name": author["name"],
                    "affiliation": author["affiliation"],
                    "orcid": rules.normalize_orcid(author["orcid"]),
                }
                for author in authors_of[meta["id"]]
            ] or None
        rows.append(
            {
                "id": meta["id"],
                "deposition_id": meta["deposition_id"],
                "title": meta["title"],
                "description": meta["description"],
                "publication_type": meta["publication_type"],
                "publication_doi": meta["publication_doi"],
                "dataset_doi": meta["dataset_doi"],
                "dataset_concept_doi": meta["dataset_concept_doi"],
                "api_publisher_user_id": publisher,
                "tags": meta["tags"],
                "ds_metrics_id": meta["ds_metrics_id"],
                "dataset_anonymous": meta["dataset_anonymous"],
                "metadata_synced": meta["metadata_synced"],
                "private_authors": None if concealed is None else json.dumps(concealed),
            }
        )
    for doi, group in sorted(owners_of_doi.items()):
        if len(group) > 1:
            ledger.conflict(
                "doi_repeated",
                "ds_meta_data",
                doi,
                group,
                detail=f"metadata {', '.join(str(m['id']) for m in group)} carry it",
            )
    return rows


def build_authors(ctx, authors, loaded_metas, anonymous_metas) -> list[dict]:
    ledger = ctx.ledger
    rows = []
    for author in authors:
        meta_id = author["ds_meta_data_id"]
        if meta_id is None or (
            meta_id not in loaded_metas
            and not ledger.is_dropped("ds_meta_data", meta_id)
        ):
            ledger.drop("author", author["id"], "orphan")
            continue
        if meta_id not in loaded_metas:
            ledger.drop(
                "author", author["id"], ledger.reason("ds_meta_data", meta_id, "orphan")
            )
            continue
        if meta_id in anonymous_metas:
            ledger.map("author", author["id"], "ds_meta_data.private_authors", meta_id)
            continue
        orcid = rules.normalize_orcid(author["orcid"])
        if author["orcid"] and orcid is None:
            ledger.note("author: ORCID not valid, NULL (C-15)")
        rows.append(
            {
                "id": author["id"],
                "name": author["name"],
                "affiliation": author["affiliation"],
                "orcid": orcid,
                "ds_meta_data_id": meta_id,
            }
        )
    return rows


def content(ctx) -> None:
    params, ledger = ctx.params, ctx.ledger
    with ctx.engine.connect() as connection:
        src = reflect(connection, params.source_schema, only=SOURCE_TABLES)
        tgt = reflect(connection, params.target_schema, only=TARGET_TABLES)
        source = {
            name: all_rows(connection, src[name], order=_order(name))
            for name in SOURCE_TABLES
        }
        connection.rollback()

    metas = {meta["id"]: meta for meta in source["ds_meta_data"]}
    files_of = defaultdict(list)
    for hubfile in source["hubfiles"]:
        files_of[hubfile["dataset_id"]].append(hubfile)
    datasets_of_meta = defaultdict(list)
    for dataset in source["datasets"]:
        datasets_of_meta[dataset["ds_meta_data_id"]].append(dataset)
    authors_of = defaultdict(list)
    for author in source["author"]:
        authors_of[author["ds_meta_data_id"]].append(author)

    chosen = choose_datasets(ctx, source["datasets"], metas, files_of)
    origins = check_lineages(ctx, source["datasets"], chosen)
    meta_rows = build_metadata(ctx, metas, datasets_of_meta, chosen, authors_of)
    loaded_metas = {row["id"] for row in meta_rows}
    anonymous_metas = {row["id"] for row in meta_rows if row["dataset_anonymous"] == 1}
    author_rows = build_authors(ctx, source["author"], loaded_metas, anonymous_metas)

    used_metrics = {
        row["ds_metrics_id"] for row in meta_rows if row["ds_metrics_id"] is not None
    }
    metric_rows = [dict(m) for m in source["ds_metrics"] if m["id"] in used_metrics]
    for metric in source["ds_metrics"]:
        if metric["id"] not in used_metrics:
            ledger.drop("ds_metrics", metric["id"], "unused")

    # Feature models, and the file that says which dataset each belongs to.
    fm_rows = {}
    for fm in source["feature_model"]:
        if fm["dataset_id"] in chosen:
            fm_rows[fm["id"]] = {"id": fm["id"], "dataset_id": fm["dataset_id"]}
    status_of = {}
    for dataset in chosen.values():
        meta = metas[dataset["ds_meta_data_id"]]
        status, visibility = state_from_metadata(
            _doi(meta),
            None if meta["metadata_synced"] is None else bool(meta["metadata_synced"]),
            meta["deposition_id"],
            meta["dataset_anonymous"],
        )
        status_of[dataset["id"]] = (status.value, visibility.value)
    first_file = {}
    for hubfile in source["hubfiles"]:
        first_file.setdefault(hubfile["feature_model_id"], hubfile)
    fms_by_id = {fm["id"]: fm for fm in source["feature_model"]}
    for fm_id, hubfile in sorted(first_file.items()):
        fm = fms_by_id.get(fm_id)
        if fm is None or fm["dataset_id"] == hubfile["dataset_id"]:
            continue
        # C-07 (P-06): the file's dataset wins.
        if hubfile["dataset_id"] in chosen:
            fm_rows[fm_id] = {"id": fm_id, "dataset_id": hubfile["dataset_id"]}
        else:
            fm_rows.pop(fm_id, None)
        involved = {fm["dataset_id"], hubfile["dataset_id"]}
        if any(status_of.get(d, ("",))[0] in PUBLISHED for d in involved):
            ledger.conflict(
                "file_two_datasets",
                "hubfiles",
                hubfile["id"],
                [hubfile, fm],
                detail=f"feature model {fm_id} is in dataset {fm['dataset_id']}, its file in {hubfile['dataset_id']}",
            )
        else:
            ledger.note("feature_model: moved to its file's dataset (C-07, drafts)")
    for fm in source["feature_model"]:
        if fm["id"] not in fm_rows:
            reason = ledger.reason("datasets", fm["dataset_id"], "dataset_not_loaded")
            ledger.drop("feature_model", fm["id"], reason)

    # Files.
    hubfile_rows = []
    paths = defaultdict(list)
    for hubfile in source["hubfiles"]:
        if hubfile["dataset_id"] not in chosen:
            reason = ledger.reason(
                "datasets", hubfile["dataset_id"], "dataset_not_loaded"
            )
            ledger.drop("hubfiles", hubfile["id"], reason)
            continue
        feature_model_id = hubfile["feature_model_id"]
        if feature_model_id not in fm_rows:
            feature_model_id = None
            ledger.note("hubfiles: feature model not loaded, NULL")
        algo = checksum_algorithm(hubfile["checksum"])
        if algo is None:
            ledger.conflict(
                "checksum_unknown",
                "hubfiles",
                hubfile["id"],
                [hubfile],
                detail=f"{hubfile['checksum']!r} is neither md5 nor sha256 (C-25)",
            )
        paths[
            (hubfile["dataset_id"], hubfile["directory_path"], hubfile["name"])
        ].append(hubfile)
        hubfile_rows.append(
            {
                "id": hubfile["id"],
                "name": hubfile["name"],
                "directory_path": hubfile["directory_path"],
                "checksum": hubfile["checksum"],
                "size": hubfile["size"],
                "dataset_id": hubfile["dataset_id"],
                "feature_model_id": feature_model_id,
                "storage_key": None,
                "storage_status": None,
                "checksum_algo": algo,
                "content_sha256": None,
                "artifact_type": rules.artifact_type(hubfile["name"]),
            }
        )
    for (dataset_id, folder, name), group in sorted(
        paths.items(), key=lambda item: str(item[0])
    ):
        if len(group) > 1:
            ledger.conflict(
                "duplicate_path",
                "hubfiles",
                f"{dataset_id}:{folder}/{name}",
                group,
                detail=f"hubfiles {', '.join(str(h['id']) for h in group)} (DM-10)",
            )
    loaded_files = {row["id"] for row in hubfile_rows}
    metric_columns = set(tgt["hubfile_metrics"].c.keys())
    hubfile_metric_rows = []
    for metric in source["hubfile_metrics"]:
        if metric["hubfile_id"] in loaded_files:
            hubfile_metric_rows.append(
                {k: v for k, v in metric.items() if k in metric_columns}
            )
        else:
            ledger.drop("hubfile_metrics", metric["hubfile_id"], "hubfile_not_loaded")

    counted = defaultdict(int)
    for fm in fm_rows.values():
        counted[fm["dataset_id"]] += 1
    dataset_rows = []
    miscounted = 0
    for dataset in chosen.values():
        meta = metas[dataset["ds_meta_data_id"]]
        status, visibility = status_of[dataset["id"]]
        doi = _doi(meta)
        miscounted += dataset["feature_model_count"] != counted[dataset["id"]]
        dataset_rows.append(
            {
                "id": dataset["id"],
                "user_id": dataset["user_id"],
                "ds_meta_data_id": dataset["ds_meta_data_id"],
                "created_at": dataset["created_at"],
                "feature_model_count": counted[dataset["id"]],
                "dataset_version": dataset["dataset_version"],
                "dataset_origin_id": origins[dataset["id"]],
                "updated_at": dataset["created_at"],
                "status": status,
                "visibility": visibility,
                "publisher_record_id": (
                    None
                    if meta["deposition_id"] is None
                    else str(meta["deposition_id"])
                ),
                "published_at": dataset["created_at"] if status in PUBLISHED else None,
                "withdrawn_at": None,
                "withdrawal_reason": None,
                "withdrawal_note": None,
                "withdrawn_by_id": None,
                "provider": (
                    LEGACY_PROVIDER
                    if doi or meta["deposition_id"] is not None
                    else None
                ),
                "pid": doi,
                "pid_scheme": DOI_SCHEME if doi else None,
                "publication_error": None,
            }
        )

    rating_rows = build_ratings(ctx, source["dataset_rating"], chosen, origins)
    transfer_rows = build_transfers(ctx, source["dataset_transfer_request"], chosen)

    with ctx.engine.connect() as connection, foreign_keys_off(connection):
        insert_batches(connection, tgt["ds_metrics"], metric_rows)
        insert_batches(connection, tgt["ds_meta_data"], meta_rows)
        insert_batches(connection, tgt["datasets"], dataset_rows)
        insert_batches(connection, tgt["author"], author_rows)
        insert_batches(connection, tgt["feature_model"], fm_rows.values())
        insert_batches(connection, tgt["hubfiles"], hubfile_rows)
        insert_batches(
            connection, tgt["hubfile_metrics"], hubfile_metric_rows, key="hubfile_id"
        )
        insert_batches(connection, tgt["dataset_rating"], rating_rows)
        insert_batches(connection, tgt["dataset_transfer_request"], transfer_rows)

    ctx.loaded.update(
        datasets=set(chosen),
        ds_meta_data=loaded_metas,
        author={row["id"] for row in author_rows},
        feature_model=set(fm_rows),
        hubfiles=loaded_files,
        dataset_rating={row["id"] for row in rating_rows},
        dataset_transfer_request={row["id"] for row in transfer_rows},
    )
    ctx.published = {d for d, (status, _v) in status_of.items() if status in PUBLISHED}
    ledger.count("ds_metrics", len(source["ds_metrics"]), len(metric_rows))
    ledger.count(
        "ds_meta_data",
        len(metas),
        len(meta_rows),
        {"tombstones": len(ledger.tombstones)},
    )
    ledger.count(
        "datasets",
        len(source["datasets"]),
        len(dataset_rows),
        {"feature_model_count_recounted": miscounted},
    )
    ledger.count("author", len(source["author"]), len(author_rows))
    ledger.count("feature_model", len(source["feature_model"]), len(fm_rows))
    ledger.count("hubfiles", len(source["hubfiles"]), len(hubfile_rows))
    ledger.count(
        "hubfile_metrics", len(source["hubfile_metrics"]), len(hubfile_metric_rows)
    )
    ledger.count("dataset_rating", len(source["dataset_rating"]), len(rating_rows))
    ledger.count(
        "dataset_transfer_request",
        len(source["dataset_transfer_request"]),
        len(transfer_rows),
        {"cancelled": ctx.facts.get("transfers_cancelled", [])},
    )
    for name, why in LATER.items():
        ledger.count(name, len(source[name]), 0, why)
    ctx.facts["statistics_v2"] = source["statistics"]
    ctx.facts["e5_first_pass"] = FIRST_PASS
    stop_on_conflicts(ctx, "E5")


def _order(name: str) -> str:
    return "hubfile_id" if name in ("hubfile_metrics", "hubfile_factlabel") else "id"


def build_ratings(ctx, ratings, chosen, origins) -> list[dict]:
    """DM-8, C-06 (P-12): each vote on the root of its lineage, the latest of
    a user's on one root wins, and a vote on one's own dataset goes."""
    ledger = ctx.ledger
    loaded_users = ctx.loaded["user"]
    by_root = defaultdict(list)
    for rating in ratings:
        if rating["dataset_id"] not in chosen:
            reason = ledger.reason(
                "datasets", rating["dataset_id"], "dataset_not_loaded"
            )
            ledger.drop("dataset_rating", rating["id"], reason)
            continue
        if rating["user_id"] not in loaded_users:
            ledger.drop(
                "dataset_rating", rating["id"], ledger.owner_reason(rating["user_id"])
            )
            continue
        root = rules.lineage_root(rating["dataset_id"], origins)
        owners = {chosen[rating["dataset_id"]]["user_id"], chosen[root]["user_id"]}
        if rating["user_id"] in owners:
            ledger.drop("dataset_rating", rating["id"], "self_vote", "DM-8")
            continue
        by_root[(rating["user_id"], root)].append(rating)
    rows = []
    for (_user, root), group in sorted(by_root.items()):
        group.sort(key=lambda r: (r["updated_at"] or r["created_at"], r["id"]))
        winner = group[-1]
        for loser in group[:-1]:
            ledger.drop(
                "dataset_rating",
                loser["id"],
                "duplicate_on_root",
                f"kept {winner['id']}",
            )
        if winner["dataset_id"] != root:
            ledger.note("dataset_rating: moved to the root of its lineage")
        rows.append(dict(winner, dataset_id=root))
    return rows


def build_transfers(ctx, transfers, chosen) -> list[dict]:
    """D13 b: every offer whose dataset and accounts load, the pending ones
    cancelled at T0 (their notices wait for RB-2, E6)."""
    params, ledger = ctx.params, ctx.ledger
    loaded_users = ctx.loaded["user"]
    rows, cancelled = [], []
    for transfer in transfers:
        if transfer["dataset_id"] not in chosen:
            reason = ledger.reason(
                "datasets", transfer["dataset_id"], "dataset_not_loaded"
            )
            ledger.drop("dataset_transfer_request", transfer["id"], reason)
            continue
        missing = [
            u
            for u in (transfer["from_user_id"], transfer["to_user_id"])
            if u not in loaded_users
        ]
        if missing:
            ledger.drop(
                "dataset_transfer_request",
                transfer["id"],
                ledger.owner_reason(missing[0]),
            )
            continue
        row = dict(transfer)
        if row["status"] == "PENDING":
            row["status"] = "CANCELLED"
            row["resolved_at"] = params.t0
            cancelled.append(row["id"])
        rows.append(row)
    ctx.facts["transfers_cancelled"] = cancelled
    return rows
