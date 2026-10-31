"""E5, content: datasets and everything hanging off them (§2.1, §4.3, §8).

It loads ds_metrics, ds_meta_data, datasets, author, feature_model,
hubfiles, hubfile_metrics, dataset_rating and dataset_transfer_request into
the tables of dataset, hubfile, uvl (which keeps featuremodel's table),
factlabel and rating, ids kept, with the rules the pinned features apply to
rows that predate them and the ones §4.3 and §8 give the content. Nothing
is left for a later pass (DEFERRED is empty): what a rule cannot settle is
a conflict, for a decision.

What it applies:

- status and visibility by dataset's own state_from_metadata (DL-1), with
  the DOI Zenodo minted for a deposition v2.12 saved none for, when the
  deposition's record in zenodo_snapshot validates (A15-04, minted_dois);
  published_at is the day Zenodo published it, its record's
  publication_date (§4.3), and created_at only while a conflict says that
  no record validates its DOI;
- the identifier as dataset0005 makes it neutral: a DOI is the pid, with
  the scheme doi, and a dataset with a DOI or a deposition is zenodo's;
- each description cleaned again by dataset's own sanitiser, as
  html_legacy (C-01, D21, DS-1), and the original of every one that
  changes in uvlhub_migration.quarantine_description, B0's where the
  hotfix D1 cleaned them in place (C-29, describe);
- publication_doi bare (C-16), and the tags split, trimmed and without
  repeats, a string still (C-23);
- the lineages a concept DOI repairs, in the order of created_at, the
  versions as they are (C-05, repair_lineages), once the curation is
  applied;
- v2.12's metrics marked legacy until factlabel extracts them again (§7.3);
- the authors of an anonymous dataset in private_authors, as dataset0003
  moves them (DS-3); an author's ORCID normalised, NULL when invalid (C-15);
  each credit as dataset 0.9.0 keeps it (DL-5): its place from 0 in the
  order of the ids, the names apart only from "Family, Given" (dataset's
  names_of, as dataset0007 reads them), and the account its iD signed in
  with (an orcid row of external_identity), none without one; no
  declaration of the co-authors, which nobody made in v2.12 (D18);
- metadata whose dataset went and left its DOI (P-01) becomes a withdrawn
  dataset, so the DOI answers dataset's tombstone, 410 with the citation,
  and not a 404 (DM-4, build_tombstones);
- the seed's datasets (P-25), ghost drafts (DM-3), metadata without a DOI
  nor a dataset (P-01) and authors of no metadata (P-02) are not loaded,
  each with its reason;
- a feature model follows its file's dataset (C-07); checksum_algo and
  artifact_type as hubfile0002 reads them (P-24); feature_model_count is
  counted again (C-12); a second file on one path gets ~<id> in its name,
  which E8 writes once the files are linked (DM-10, plan_renames);
- votes move to the root of their lineage, the latest of a user's wins and
  self-votes go (DM-8, C-06); pending transfers are cancelled at T0 (D13 b),
  their notices held by E6;
- each dataset's public id (CO-5, §4.2), a ULID of its created_at whose 80
  random bits are the first of HMAC-SHA256(MIGRATION_PUBLIC_ID_KEY,
  "dataset:<id>"), so every run gives each dataset the same one; the root
  of its lineage as it loads (its own id for an original), and its
  concept_pid from its metadata's concept DOI, as dataset0009 fills them.

What it finds and leaves open, as conflicts for a decision, as the plan
has them: DOIs that are not Zenodo's production, not their deposition's or
of no record that validates (C-30), a deposition without a DOI whose record
is another's (C-09), DOIs or metadata shared by two datasets (C-10, P-03,
"resolución manual"), lineages with a missing origin, branches or gaps that
no concept DOI repairs (C-05), checksums of no known algorithm (C-25), a
file whose feature model is in another, published dataset (C-07), and a
tombstone no Zenodo record dates or nobody can hold (DM-4).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections import Counter, defaultdict
from datetime import timedelta

import sqlalchemy as sa
from splent_io.splent_feature_dataset.authors import names_of
from splent_io.splent_feature_dataset.descriptions import HTML_LEGACY, clean_html
from splent_io.splent_feature_dataset.public_ids import new_public_id
from splent_io.splent_feature_dataset.models import (
    DOI_SCHEME,
    LEGACY_PROVIDER,
    DatasetStatus,
    WithdrawalReason,
    state_from_metadata,
)
from splent_io.splent_feature_hubfile.storage import checksum_algorithm

from uvlhub_splent.migration_v2 import curation, rules
from uvlhub_splent.migration_v2.db import (
    all_rows,
    foreign_keys_off,
    insert_batches,
    qualified,
    reflect,
)
from uvlhub_splent.migration_v2.identity import PROVIDERS
from uvlhub_splent.migration_v2.ledger import stop_on_conflicts, to_json

# The final pass: what the first one left (the descriptions, the lineages by
# concept DOI, Zenodo's dates and minted DOIs, the publication DOI and the
# tags, the legacy metrics) is done, and DEFERRED says nothing, so a run
# with nothing else pending is ready for the cutover (report.py).
FIRST_PASS = False

DEFERRED: tuple[str, ...] = ()

# The revision of the hotfix D1 that cleaned every description in place,
# keeping no copy (f7a8b9c0d1e2_sanitize_stored_descriptions): on a source
# at this head the originals are B0's (C-29).
HOTFIX_HEAD = "f7a8b9c0d1e2"

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
    "statistics",
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
# What E9 rebuilds or nothing keeps, counted here so the report says it.
LATER = {
    "hubfile_factlabel": "E9: recomputed (DM-6)",
    "statistics": "dropped (DC-7): its counters are in the report",
}
PUBLISHED = (DatasetStatus.PUBLISHED.value, DatasetStatus.SYNC_PENDING.value)
# The provider of external_identity whose provider_id is an ORCID iD.
ORCID_PROVIDER = PROVIDERS[0]
# DM-4: what the tombstone of a dataset deleted in v2.12 says. "other" is
# none of the reasons the law decides (451) or that mark abuse, which
# curation reads to stop trusting an account.
TOMBSTONE_REASON = WithdrawalReason.OTHER.value
TOMBSTONE_NOTE = (
    "Deleted from uvlhub.io before it moved to uvlhub 3.0. Its DOI stays, and "
    "so does its record at Zenodo."
)


def _doi(meta) -> str | None:
    return (meta["dataset_doi"] or "").strip() or None


def linked_accounts(connection, schema) -> dict[str, int]:
    """The account each ORCID iD signed in with, by iD: the orcid rows E4
    loaded into external_identity, whose provider_id is the iD normalised."""
    rows = connection.execute(
        sa.text(
            f"SELECT provider_id, user_id FROM {qualified(schema, 'external_identity')} "
            "WHERE provider = :provider"
        ),
        {"provider": ORCID_PROVIDER},
    ).all()
    return dict(rows)


def credit(author, linked) -> dict:
    """An author of v2.12 as dataset 0.9.0 credits it (Author.entry, DL-5):
    the names apart only from "Family, Given" with one comma (names_of, as
    dataset0007 reads them), and the account its iD signed in with, if any."""
    orcid = rules.normalize_orcid(author["orcid"])
    given, family = names_of(author["name"] or "")
    return {
        "name": author["name"],
        "given_name": given,
        "family_name": family,
        "affiliation": author["affiliation"],
        "orcid": orcid,
        "user_id": linked.get(orcid) if orcid else None,
    }


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


def minted_dois(ctx, metas, datasets_of_meta, chosen, snapshots) -> dict[int, str]:
    """§4.3, A15-04 (C-09): the DOI Zenodo minted for a deposition v2.12
    saved none for, by metadata id, where the deposition's record in
    zenodo_snapshot shows Zenodo published it (rules.minted_record).

    v2.12 lost the DOI when Zenodo answered late or the request broke after
    the publication (A05-02). With it the dataset is published as any
    other, and a metadata whose dataset v2.12 deleted becomes a tombstone
    (DM-4). Only the metadata that load are asked: a dataset that loads, or
    none at all. A deposition with no record stays failed, the public API's
    404 for one Zenodo never published; a record that is another's is a
    conflict, and it stays failed."""
    minted = {}
    for meta in metas.values():
        if _doi(meta) is not None or meta["deposition_id"] is None:
            continue
        datasets = datasets_of_meta[meta["id"]]
        if datasets and not any(d["id"] in chosen for d in datasets):
            continue
        record, why = rules.minted_record(
            snapshots.get(meta["deposition_id"]), meta["deposition_id"], meta["title"]
        )
        if record is not None:
            minted[meta["id"]] = record["doi"].strip()
        elif why is not None:
            ctx.ledger.conflict(
                "deposition_record_mismatch",
                "ds_meta_data",
                meta["deposition_id"],
                [meta],
                detail=f"{why} (§4.3): it loads as failed",
            )
    ctx.facts["dois_minted_by_zenodo"] = {
        "datasets": sorted(
            d["id"]
            for meta_id in minted
            for d in datasets_of_meta[meta_id]
            if d["id"] in chosen
        ),
        "metadata_without_dataset": sorted(
            meta_id for meta_id in minted if not datasets_of_meta[meta_id]
        ),
    }
    return minted


def _one_chain(members) -> bool:
    """Whether ``members`` stand on one another already, one line from one
    first version: then there is nothing to repair, whatever their dates."""
    inside = {d["id"] for d in members}
    firsts = [d for d in members if d["dataset_origin_id"] not in inside]
    claimed = Counter(
        d["dataset_origin_id"] for d in members if d["dataset_origin_id"] in inside
    )
    return len(firsts) == 1 and all(n == 1 for n in claimed.values())


def repair_lineages(ctx, chosen, metas, concepts):
    """C-05 (P-04, P-05, MIG-06): the datasets that load, with the lineages
    their concept DOIs repair, and the rows of uvlhub_migration.curated that
    say so.

    Every version of a lineage shares its concept DOI at Zenodo (§4.3), the
    one v2.12 kept or the one its record gives (zenodo_concepts). The
    datasets of one concept that are not one line already are made one by
    rules.concept_chain: by created_at, each on the one before,
    dataset_version as it is. Where the versions do not rise with the
    dates, nothing changes, and check_lineages finds what is left. The
    lineages the curation made (RU-06) are a decision, and stay as it left
    them."""
    curated_ids = {
        member[0]
        for lineage in (ctx.facts.get("curation") or {}).get("lineages", [])
        for member in lineage["after"]
    }
    groups = defaultdict(list)
    for dataset in chosen.values():
        meta_id = dataset["ds_meta_data_id"]
        concept = (metas[meta_id]["dataset_concept_doi"] or "").strip() or (
            concepts.get(meta_id)
        )
        if concept and dataset["id"] not in curated_ids:
            groups[concept].append(dataset)
    repaired, changes, done, left = dict(chosen), [], [], []
    for concept, members in sorted(groups.items()):
        if len(members) < 2 or _one_chain(members):
            continue
        chain = rules.concept_chain(members)
        if chain is None:
            left.append(
                {
                    "concept": concept,
                    "datasets": sorted(d["id"] for d in members),
                    "why": "its versions do not rise with their created_at",
                }
            )
            continue
        for dataset_id, origin in chain:
            dataset = chosen[dataset_id]
            if dataset["dataset_origin_id"] == origin:
                continue
            repaired[dataset_id] = dict(dataset, dataset_origin_id=origin)
            changes.append(
                {
                    "dataset_id": dataset_id,
                    "lineage": f"C-05 {concept}",
                    "old_origin_id": dataset["dataset_origin_id"],
                    "old_version": dataset["dataset_version"],
                    "origin_id": origin,
                    "version": dataset["dataset_version"],
                }
            )
        done.append({"concept": concept, "chain": [list(link) for link in chain]})
    ctx.facts["lineages_by_concept"] = {"repaired": done, "left": left}
    return repaired, changes


def describe(ctx, meta_rows, metas) -> list[dict]:
    """C-01, C-29 (D21, DS-1, DM-12): every description loaded as
    html_legacy, cleaned again by dataset's own sanitiser
    (descriptions.clean_html, its allowlist outside an app the default,
    which is the one uvlhub sets), as dataset0010 cleaned the rows there
    were. That is the text v2.12 has now, as the plan's §2.1 says ("se
    re-sanea desde el texto vigente"): what uvlhub.io shows today stays.

    The original of every description the migration changes goes to
    uvlhub_migration.quarantine_description with what was loaded (C-01):
    on a source at the hotfix's head, B0's, since the hotfix cleaned them in
    place (C-29); without B0 there, what the hotfix took out is lost, which
    the report says, and the text it left is the original kept. Answers the
    rows of quarantine_description.

    The report gives the plan's two classes of what changed: formatting,
    and active content (a script, a handler, a javascript: address), whose
    cases a curator reads; and how many descriptions use each element
    (P-22), which tells whether uvlhub should let images in (D21)."""
    originals = ctx.b0 or {}
    hotfixed = ctx.params.expected_head == HOTFIX_HEAD
    quarantine, active, formatting = [], [], []
    elements = Counter()
    for row in meta_rows:
        current = metas[row["id"]]["description"] or ""
        original = originals.get(row["id"], current)
        loaded = str(clean_html(current)).strip()
        row["description"] = loaded
        row["description_format"] = HTML_LEGACY
        found = rules.markup(original)
        elements.update(found.tags)
        if found.active:
            active.append(row["id"])
        if original != loaded:
            quarantine.append(
                {
                    "ds_meta_data_id": row["id"],
                    "original": original,
                    "sanitized": loaded,
                }
            )
            if not found.active:
                formatting.append(row["id"])
    if ctx.b0 is not None:
        source = "b0"
    elif hotfixed:
        source = "lost"
        ctx.alerts.append(
            "C-29: the source is at the hotfix's head and no B0 was given "
            "(--b0): what the hotfix took out of the descriptions is lost, and "
            "quarantine_description keeps the text it left"
        )
    else:
        source = "source"
    ctx.facts["descriptions"] = {
        "format": HTML_LEGACY,
        "originals": source,
        "b0_differs": None
        if ctx.b0 is None
        else sorted(
            row["id"]
            for row in meta_rows
            if row["id"] in originals
            and originals[row["id"]] != (metas[row["id"]]["description"] or "")
        ),
        "quarantined": len(quarantine),
        "formatting": len(formatting),
        "active_content": sorted(active),
        "elements": dict(sorted(elements.items())),
    }
    if quarantine:
        ctx.ledger.note(
            "ds_meta_data: description other than its original, quarantined (C-01)",
            len(quarantine),
        )
    return quarantine


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
                [dataset] + ([by_id[origin]] if origin in by_id else []),
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


def public_id_of(key: str, dataset_id: int, created_at) -> str:
    """§4.2: the public id of dataset ``dataset_id``, the same every run:
    the time of ``created_at`` and the first 80 bits of
    HMAC-SHA256(``key``, "dataset:<id>")."""
    digest = hmac.new(
        key.encode("utf-8"), f"dataset:{dataset_id}".encode(), hashlib.sha256
    ).digest()
    return new_public_id(created_at, randomness=int.from_bytes(digest[:10], "big"))


def lineage_roots(origins: dict[int, int | None]) -> dict[int, int]:
    """The root of each loaded dataset's lineage, by its origins as they
    load (check_lineages): its own id for an original, and for a row whose
    origins run in a circle, as dataset0009 does."""
    roots = {}
    for dataset_id in origins:
        seen, node = [dataset_id], origins[dataset_id]
        while node is not None and node in origins and node not in seen:
            seen.append(node)
            node = origins[node]
        roots[dataset_id] = dataset_id if node in seen else seen[-1]
    return roots


def identify(ctx, dataset_rows, metas, origins, concepts) -> None:
    """CO-5, DL-9, CT-4: each row's public_id, lineage_root_id and
    concept_pid, its metadata's concept DOI or the one Zenodo gives."""
    roots = lineage_roots(origins)
    key = ctx.params.public_id_key
    for row in dataset_rows:
        meta_id = row["ds_meta_data_id"]
        concept = (metas[meta_id]["dataset_concept_doi"] or "").strip() or (
            concepts.get(meta_id) or ""
        )
        row["public_id"] = public_id_of(key, row["id"], row["created_at"])
        row["lineage_root_id"] = roots.get(row["id"], row["id"])
        row["concept_pid"] = concept or None


def zenodo_concepts(ctx, metas, datasets_of_meta, snapshots, dois) -> dict[int, str]:
    """§4.3, CT-4: the concept DOI of every metadata with a DOI (``dois``,
    the minted ones too) and none of its own, from its record in
    zenodo_snapshot when the record validates, by metadata id. A concept
    DOI v2.12 kept is never changed."""
    found = {}
    for meta in metas.values():
        doi = dois.get(meta["id"])
        if doi is None or (meta["dataset_concept_doi"] or "").strip():
            continue
        concept = rules.zenodo_concept(snapshots.get(meta["deposition_id"]), doi)
        if concept:
            found[meta["id"]] = concept
    ctx.facts["concepts_from_zenodo"] = sorted(
        dataset["id"] for meta_id in found for dataset in datasets_of_meta[meta_id]
    )
    return found


def build_metadata(
    ctx,
    metas,
    datasets_of_meta,
    chosen,
    tombstones,
    authors_of,
    linked,
    concepts,
    dois,
    snapshots,
):
    """ds_meta_data rows of the loaded datasets and of the tombstones;
    metadata of neither dropped (P-01); DOIs checked (C-10, C-30): a DOI of
    Zenodo's production, the one it mints for the deposition, whose record
    in zenodo_snapshot validates (§4.3; a tombstone's record dates it,
    build_tombstones). ``dois`` holds each one's DOI, the minted ones too
    (minted_dois), which the row takes. publication_doi bare (C-16), tags
    without blanks or repeats (C-23)."""
    ledger = ctx.ledger
    loaded_users = ctx.loaded["user"]
    rows = []
    owners_of_doi = defaultdict(list)
    for meta in metas.values():
        datasets = datasets_of_meta[meta["id"]]
        loading = [d for d in datasets if d["id"] in chosen]
        if not datasets and meta["id"] not in tombstones:
            if not ledger.is_dropped("ds_meta_data", meta["id"]):
                ledger.drop("ds_meta_data", meta["id"], "orphan")
            continue
        if datasets and not loading:
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
                {"ds_meta_data": [meta], "datasets": datasets},
                detail=f"datasets {', '.join(str(d['id']) for d in datasets)} share it",
            )
        doi = dois.get(meta["id"])
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
            elif not rules.doi_is_of_deposition(doi, meta["deposition_id"]):
                ledger.conflict(
                    "doi_not_its_deposition",
                    "ds_meta_data",
                    doi,
                    [meta],
                    detail=f"deposition {meta['deposition_id']} mints another DOI",
                )
            elif (
                loading
                and rules.zenodo_record(snapshots.get(meta["deposition_id"]), doi)
                is None
            ):
                ledger.conflict(
                    "doi_record_missing",
                    "ds_meta_data",
                    doi,
                    [meta],
                    detail="no record of zenodo_snapshot validates it: not "
                    "fetched (zenodo-snapshot), gone from Zenodo (404, 410) or "
                    "another DOI's (§4.3)",
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
                credit(author, linked) for author in authors_of[meta["id"]]
            ] or None
        publication_doi = rules.publication_doi(meta["publication_doi"])
        if publication_doi != meta["publication_doi"]:
            ledger.note("ds_meta_data: publication_doi normalised (C-16)")
        elif publication_doi and rules.publication_doi_of(publication_doi) is None:
            ledger.note(
                "ds_meta_data: publication_doi neither a DOI nor an address, "
                "kept as it is (C-16)"
            )
        tags = rules.normal_tags(meta["tags"])
        if tags != meta["tags"]:
            ledger.note("ds_meta_data: tags split, trimmed and without repeats (C-23)")
        rows.append(
            {
                "id": meta["id"],
                "deposition_id": meta["deposition_id"],
                "title": meta["title"],
                # describe() cleans it once every row is here (C-01).
                "description": meta["description"],
                "description_format": HTML_LEGACY,
                "publication_type": meta["publication_type"],
                "publication_doi": publication_doi,
                # The minted DOI where v2.12 saved none (A15-04), else
                # v2.12's as it is (V-02 compares it byte for byte).
                "dataset_doi": meta["dataset_doi"]
                if _doi(meta) is not None
                else doi or meta["dataset_doi"],
                "dataset_concept_doi": meta["dataset_concept_doi"]
                or concepts.get(meta["id"]),
                "api_publisher_user_id": publisher,
                "tags": tags,
                "ds_metrics_id": meta["ds_metrics_id"],
                "dataset_anonymous": meta["dataset_anonymous"],
                "metadata_synced": meta["metadata_synced"],
                "private_authors": None if concealed is None else json.dumps(concealed),
                # D18: nobody declared anything in v2.12, and nothing asks
                # the depositors to now.
                "authors_declared_at": None,
                "authors_declared_by_id": None,
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


def build_tombstones(ctx, metas, datasets_of_meta, datasets, snapshots, dois):
    """DM-4 (C-03, P-01): a withdrawn dataset for each metadata whose
    dataset v2.12 deleted and left its DOI behind, so the DOI answers
    dataset's tombstone (landing_response), 410 with the citation its
    metadata and authors make, instead of a 404. The DOI is ``dois``'s:
    v2.12's, or the one Zenodo minted when v2.12 saved none (A15-04,
    minted_dois). Answers the rows by metadata id; every one is in
    uvlhub_migration.tombstone too.

    v2.12 kept no date of them: Zenodo's record in zenodo_snapshot gives
    created_at and published_at, which the citation's year is; without it,
    T0, and a conflict. Its owner is gone with it: the administrator
    MIGRATION_ADMIN_EMAILS names first holds it (DM-13), and without one
    loaded nothing is made, and that is a conflict too. Its id is a new one
    above the source's counter of datasets, as no dataset of v2.12 has it.
    """
    params, ledger = ctx.params, ctx.ledger
    owner = ctx.admins[0] if ctx.admins else None
    counter = ctx.source_counters.get("datasets")
    next_id = max(counter or 1, max((d["id"] for d in datasets), default=0) + 1)
    rows = {}
    for meta in metas.values():
        doi = dois.get(meta["id"])
        if datasets_of_meta[meta["id"]] or doi is None:
            continue
        tombstone = {
            "doi": doi,
            "ds_meta_data_id": meta["id"],
            "dataset_id": None,
            "snapshot": to_json(meta),
        }
        ledger.tombstones.append(tombstone)
        if owner is None:
            ledger.conflict(
                "tombstone_without_owner",
                "ds_meta_data",
                doi,
                [meta],
                detail="no account of MIGRATION_ADMIN_EMAILS loads to hold it",
            )
            ledger.drop("ds_meta_data", meta["id"], "tombstone", doi)
            continue
        dates = rules.zenodo_dates(snapshots.get(meta["deposition_id"]), doi)
        if dates is None:
            ledger.conflict(
                "tombstone_undated",
                "ds_meta_data",
                doi,
                [meta],
                detail="no record of zenodo_snapshot dates it: it is dated T0, "
                "and its citation gives T0's year",
            )
            created, published = params.t0, None
        else:
            created, published = dates
        _status, visibility = state_from_metadata(
            doi, True, meta["deposition_id"], meta["dataset_anonymous"]
        )
        rows[meta["id"]] = {
            "id": next_id,
            "user_id": owner,
            "ds_meta_data_id": meta["id"],
            "created_at": created,
            "feature_model_count": 0,
            "dataset_version": 1,
            "dataset_origin_id": None,
            "updated_at": created,
            "status": DatasetStatus.WITHDRAWN.value,
            "visibility": visibility.value,
            "publisher_record_id": (
                None if meta["deposition_id"] is None else str(meta["deposition_id"])
            ),
            "published_at": published,
            "withdrawn_at": None,
            "withdrawal_reason": TOMBSTONE_REASON,
            "withdrawal_note": TOMBSTONE_NOTE,
            "withdrawn_by_id": None,
            "provider": LEGACY_PROVIDER,
            "pid": doi,
            "pid_scheme": DOI_SCHEME,
            "publication_error": None,
        }
        tombstone["dataset_id"] = next_id
        ledger.map("tombstone", meta["id"], "datasets", next_id)
        next_id += 1
    return rows


def plan_renames(ctx, paths) -> list[dict]:
    """DM-10 (C-11, P-07): on a path more than one file of a dataset has,
    the first by id keeps its name, the one v2.12 served at
    /doi/<doi>/files/raw/<path>, and every other gets ~<id> before its
    extension. E8 writes the names once storage-migrate has linked the
    files, which it finds by their v2.12 names, and hubfile's hubfile_alias
    keeps the old name of each, whose /hubfiles/raw/<id>/<name> answers a
    308 to the new one. A new name that is another file's is a conflict,
    and that row keeps its name."""
    column = ctx.contract.tables["hubfiles"].columns["name"]
    limit = int(column.type.split("(")[1].rstrip(")"))
    renames = []
    for (dataset_id, folder, name), group in sorted(
        paths.items(), key=lambda item: str(item[0])
    ):
        if len(group) < 2:
            continue
        for hubfile in sorted(group, key=lambda h: h["id"])[1:]:
            new_name = rules.suffixed_name(name, hubfile["id"], limit)
            if (dataset_id, folder, new_name) in paths:
                ctx.ledger.conflict(
                    "duplicate_path",
                    "hubfiles",
                    f"{dataset_id}:{folder}/{name}",
                    group,
                    detail=f"{new_name} is another file's (DM-10)",
                )
                continue
            renames.append(
                {
                    "hubfile_id": hubfile["id"],
                    "dataset_id": dataset_id,
                    "directory_path": folder,
                    "old_name": name,
                    "new_name": new_name,
                }
            )
    return renames


def build_authors(ctx, authors, loaded_metas, anonymous_metas, linked) -> list[dict]:
    """The author rows, each at its place in its metadata's credit, from 0
    in the order of the ids (dataset0007)."""
    ledger = ctx.ledger
    rows = []
    places = defaultdict(int)
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
        row = credit(author, linked)
        if author["orcid"] and row["orcid"] is None:
            ledger.note("author: ORCID not valid, NULL (C-15)")
        if row["user_id"] is not None:
            ledger.note("author: linked to the account its ORCID iD signed in with")
        rows.append(
            dict(
                row,
                id=author["id"],
                position=places[meta_id],
                ds_meta_data_id=meta_id,
            )
        )
        places[meta_id] += 1
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
        snapshots = {
            row["deposition_id"]: row
            for row in all_rows(
                connection, ctx.inputs["zenodo_snapshot"], order="deposition_id"
            )
        }
        linked = linked_accounts(connection, params.target_schema)
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
    # A15-04: the DOIs v2.12 lost, and every metadata's DOI with them.
    minted = minted_dois(ctx, metas, datasets_of_meta, chosen, snapshots)
    dois = {
        meta_id: _doi(meta) or minted.get(meta_id) for meta_id, meta in metas.items()
    }
    # RU-06: the lineages the curation makes, then the ones the concept DOIs
    # repair (C-05), before they are checked.
    chosen, curated = curation.apply(ctx, chosen, metas, snapshots)
    concepts = zenodo_concepts(ctx, metas, datasets_of_meta, snapshots, dois)
    chosen, repaired = repair_lineages(ctx, chosen, metas, concepts)
    origins = check_lineages(ctx, source["datasets"], chosen)
    tombstones = build_tombstones(
        ctx, metas, datasets_of_meta, source["datasets"], snapshots, dois
    )
    meta_rows = build_metadata(
        ctx,
        metas,
        datasets_of_meta,
        chosen,
        tombstones,
        authors_of,
        linked,
        concepts,
        dois,
        snapshots,
    )
    quarantine = describe(ctx, meta_rows, metas)
    loaded_metas = {row["id"] for row in meta_rows}
    anonymous_metas = {row["id"] for row in meta_rows if row["dataset_anonymous"] == 1}
    author_rows = build_authors(
        ctx, source["author"], loaded_metas, anonymous_metas, linked
    )

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
            dois[meta["id"]],
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
                {"hubfiles": [hubfile], "feature_model": [fm]},
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
    ctx.renames = plan_renames(ctx, paths)
    loaded_files = {row["id"] for row in hubfile_rows}
    metric_columns = set(tgt["hubfile_metrics"].c.keys())
    version_limit = tgt["hubfile_metrics"].c.extractor_version.type.length
    hubfile_metric_rows = []
    for metric in source["hubfile_metrics"]:
        if metric["hubfile_id"] in loaded_files:
            row = {k: v for k, v in metric.items() if k in metric_columns}
            # §7.3: legacy until factlabel extracts it again (E9, or
            # metrics-backfill once 3.0 is up).
            row["extractor_version"] = rules.legacy_extractor_version(
                metric["extractor_version"], version_limit
            )
            hubfile_metric_rows.append(row)
        else:
            ledger.drop("hubfile_metrics", metric["hubfile_id"], "hubfile_not_loaded")
    if hubfile_metric_rows:
        ledger.note(
            "hubfile_metrics: v2.12's, legacy until extracted again (§7.3)",
            len(hubfile_metric_rows),
        )

    counted = defaultdict(int)
    for fm in fm_rows.values():
        counted[fm["dataset_id"]] += 1
    dataset_rows = []
    miscounted = 0
    zenodo_dated, undated = 0, []
    for dataset in chosen.values():
        meta = metas[dataset["ds_meta_data_id"]]
        status, visibility = status_of[dataset["id"]]
        doi = dois[meta["id"]]
        miscounted += dataset["feature_model_count"] != counted[dataset["id"]]
        published_at = None
        if status in PUBLISHED:
            # §4.3: the day Zenodo published it, what its citation's year
            # is; v2.12's created_at only while doi_record_missing is open.
            dates = rules.zenodo_dates(snapshots.get(meta["deposition_id"]), doi)
            if dates is None:
                published_at = dataset["created_at"]
                undated.append(dataset["id"])
            else:
                published_at = dates[1]
                zenodo_dated += 1
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
                "published_at": published_at,
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
    dataset_rows += tombstones.values()
    ctx.facts["published_at"] = {"zenodo": zenodo_dated, "created_at": sorted(undated)}
    identify(ctx, dataset_rows, metas, origins, concepts)

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
        insert_batches(
            connection, ctx.outputs["curated"], curated + repaired, key="dataset_id"
        )
        insert_batches(
            connection,
            ctx.outputs["quarantine_description"],
            quarantine,
            key="ds_meta_data_id",
        )

    ctx.loaded.update(
        datasets=set(chosen) | {row["id"] for row in tombstones.values()},
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
        {"feature_model_count_recounted": miscounted, "tombstones": len(tombstones)},
    )
    ledger.count("author", len(source["author"]), len(author_rows))
    ledger.count("feature_model", len(source["feature_model"]), len(fm_rows))
    ledger.count(
        "hubfiles",
        len(source["hubfiles"]),
        len(hubfile_rows),
        {"renamed": [r["hubfile_id"] for r in ctx.renames]},
    )
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
        row = dict(transfer, cancel_reason=None)
        if row["status"] == "PENDING":
            row["status"] = "CANCELLED"
            row["resolved_at"] = params.t0
            row["cancel_reason"] = "migration"
            cancelled.append(row["id"])
        rows.append(row)
    ctx.facts["transfers_cancelled"] = cancelled
    return rows
