"""RU-06: the curation decided with the rows in front, an input of E5.

uvlhub.io published some datasets more than once, each time as a new
record with a DOI of its own. ``curation.toml`` says what becomes of them,
and E5 applies it as it loads, never by hand on the database:

- ``[[lineage]]``: published datasets that are one dataset become the
  versions of one lineage, in the order Zenodo published them (the time
  of their record in zenodo_snapshot when it validates, else v2.12's
  created_at, then the id). Each keeps its own DOI and its own concept
  DOI, so every DOI still lands on its record (lineage.py resolves a
  concept to the versions that carry it); the first is the root, each one
  stands on the one before (dataset_origin_id) and is numbered from 1
  (dataset_version), so explore shows the lineage once, as its newest
  version. Votes follow, as they do for any lineage (DM-8).
- ``[[draft]]``: drafts that duplicate other datasets. A draft is its
  owner's: nothing is hidden or dropped; the report lists them for their
  owners, who may want to remove them.
- ``[[review]]``: datasets that look alike and are left as they are, for
  someone to decide (other owners, or other content under one title).

Every dataset is named by its id, and a member of a lineage also by the
DOI it was published under: a rule never applies to other rows than the
ones it was decided on, and one that does not hold stops the run (zero
unknowns). uvlhub_migration.curated keeps the place each dataset had in
v2.12 and the one it was given.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from splent_io.splent_feature_dataset.models import DatasetStatus, state_from_metadata

from uvlhub_splent.migration_v2 import rules
from uvlhub_splent.migration_v2.params import Refused

#: The decisions R1 took on uvlhub.io's datasets.
CURATION = Path(__file__).with_name("curation.toml")

PUBLISHED = (DatasetStatus.PUBLISHED.value, DatasetStatus.SYNC_PENDING.value)


@dataclass(frozen=True)
class Lineage:
    name: str
    # (dataset id, DOI), in the file's order; E5 orders them by date.
    members: tuple[tuple[int, str], ...]


@dataclass(frozen=True)
class Listed:
    datasets: tuple[int, ...]
    # The datasets a draft duplicates.
    of: tuple[int, ...] = ()
    why: str = ""


@dataclass(frozen=True)
class Curation:
    lineages: tuple[Lineage, ...] = ()
    drafts: tuple[Listed, ...] = ()
    review: tuple[Listed, ...] = ()


def _ids(values, where: str) -> tuple[int, ...]:
    if not isinstance(values, list) or not values:
        raise ValueError(f"{where}: a list of dataset ids")
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in values):
        raise ValueError(f"{where}: dataset ids are integers")
    return tuple(values)


def parse(data: dict) -> Curation:
    lineages, seen = [], {}
    for index, entry in enumerate(data.get("lineage", []), 1):
        name = entry.get("name") or f"lineage {index}"
        members = []
        for member in entry.get("members") or []:
            dataset_id, doi = member.get("id"), (member.get("doi") or "").strip()
            if not isinstance(dataset_id, int) or not doi:
                raise ValueError(f"{name}: every member has an id and a DOI")
            if dataset_id in seen:
                raise ValueError(
                    f"dataset {dataset_id} is in {seen[dataset_id]} and in {name}"
                )
            seen[dataset_id] = name
            members.append((dataset_id, doi))
        if len(members) < 2:
            raise ValueError(f"{name}: a lineage of one dataset is no curation")
        lineages.append(Lineage(name, tuple(members)))
    drafts = tuple(
        Listed(
            _ids(entry.get("datasets"), "draft"),
            tuple(entry.get("of") or ()),
            entry.get("why", ""),
        )
        for entry in data.get("draft", [])
    )
    review = tuple(
        Listed(_ids(entry.get("datasets"), "review"), (), entry.get("why", ""))
        for entry in data.get("review", [])
    )
    return Curation(tuple(lineages), drafts, review)


def load(path: Path | None) -> Curation:
    """The curation in ``path``; none without one. ValueError when it does
    not say what this module reads."""
    if path is None:
        return Curation()
    with open(path, "rb") as handle:
        try:
            data = tomllib.load(handle)
        except tomllib.TOMLDecodeError as error:
            raise ValueError(f"{path}: {error}") from error
    if data.get("version") != 1:
        raise ValueError(f"{path}: version 1 is the one this migrator reads")
    return parse(data)


def _status(meta) -> str:
    status, _visibility = state_from_metadata(
        (meta["dataset_doi"] or "").strip() or None,
        None if meta["metadata_synced"] is None else bool(meta["metadata_synced"]),
        meta["deposition_id"],
        meta["dataset_anonymous"],
    )
    return status.value


def published_order(dataset, meta, snapshots):
    """When Zenodo published ``dataset``: its record's time when the record
    validates, else v2.12's created_at; the id breaks ties."""
    doi = (meta["dataset_doi"] or "").strip()
    dates = rules.zenodo_dates(snapshots.get(meta["deposition_id"]), doi)
    return (dates[0] if dates else dataset["created_at"], dataset["id"])


def apply(ctx, chosen: dict, metas: dict, snapshots: dict):
    """``chosen`` (the datasets that load, by id) with the lineages of the
    curation, as copies, the rest as they are; and the rows of
    uvlhub_migration.curated. Refused when a rule does not hold for the rows
    the source has."""
    curation = load(ctx.params.curation)
    problems = []

    def check(dataset_id, what):
        if dataset_id not in chosen:
            problems.append(f"RU-06 {what}: dataset {dataset_id} does not load")
            return None
        return chosen[dataset_id]

    curated = dict(chosen)
    changes, lineages = [], []
    members_of = {
        dataset_id: lineage.name
        for lineage in curation.lineages
        for dataset_id, _doi in lineage.members
    }
    for lineage in curation.lineages:
        rows = []
        for dataset_id, doi in lineage.members:
            dataset = check(dataset_id, lineage.name)
            if dataset is None:
                continue
            meta = metas[dataset["ds_meta_data_id"]]
            if (meta["dataset_doi"] or "").strip().lower() != doi.lower():
                problems.append(
                    f"RU-06 {lineage.name}: dataset {dataset_id} is not {doi}"
                )
            elif _status(meta) not in PUBLISHED:
                problems.append(
                    f"RU-06 {lineage.name}: dataset {dataset_id} is not published"
                )
            origin = dataset["dataset_origin_id"]
            if origin is not None and members_of.get(origin) != lineage.name:
                problems.append(
                    f"RU-06 {lineage.name}: dataset {dataset_id} stands on "
                    f"{origin}, which the lineage does not name"
                )
            rows.append(dataset)
        names = {dataset_id for dataset_id, _doi in lineage.members}
        for dataset in chosen.values():
            if dataset["id"] not in names and dataset["dataset_origin_id"] in names:
                problems.append(
                    f"RU-06 {lineage.name}: dataset {dataset['id']} is a version "
                    f"of {dataset['dataset_origin_id']} and the lineage does not "
                    "name it"
                )
        if len({d["user_id"] for d in rows}) > 1:
            problems.append(
                f"RU-06 {lineage.name}: its datasets are of more than one account, "
                "and a lineage has one owner"
            )
        if len(rows) != len(lineage.members):
            continue
        rows.sort(
            key=lambda d: published_order(d, metas[d["ds_meta_data_id"]], snapshots)
        )
        before = [
            [d["id"], d["dataset_origin_id"], d["dataset_version"]]
            for d in sorted(rows, key=lambda d: d["id"])
        ]
        after, origin = [], None
        for version, dataset in enumerate(rows, 1):
            curated[dataset["id"]] = dict(
                dataset, dataset_origin_id=origin, dataset_version=version
            )
            after.append([dataset["id"], origin, version])
            if (dataset["dataset_origin_id"], dataset["dataset_version"]) != (
                origin,
                version,
            ):
                changes.append(
                    {
                        "dataset_id": dataset["id"],
                        "lineage": lineage.name,
                        "old_origin_id": dataset["dataset_origin_id"],
                        "old_version": dataset["dataset_version"],
                        "origin_id": origin,
                        "version": version,
                    }
                )
            origin = dataset["id"]
        lineages.append({"name": lineage.name, "before": before, "after": after})

    for listed in curation.drafts:
        for dataset_id in listed.datasets:
            dataset = check(dataset_id, "draft")
            if dataset is not None and (
                _status(metas[dataset["ds_meta_data_id"]]) in PUBLISHED
            ):
                problems.append(f"RU-06 draft: dataset {dataset_id} is published")
        for dataset_id in listed.of:
            check(dataset_id, "draft")
    for listed in curation.review:
        for dataset_id in listed.datasets:
            check(dataset_id, "review")
    if problems:
        raise Refused("E5", problems)

    ctx.facts["curation"] = {
        "file": None if ctx.params.curation is None else str(ctx.params.curation),
        "lineages": lineages,
        "changed": len(changes),
        "drafts_that_duplicate": [
            {"datasets": list(d.datasets), "of": list(d.of), "why": d.why}
            for d in curation.drafts
        ],
        "manual_review": [
            {"datasets": list(r.datasets), "why": r.why} for r in curation.review
        ],
    }
    return curated, changes
