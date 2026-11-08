"""RU-06: the curation E5 applies, read from its file and held to the rows.

The lineages it makes, in the order Zenodo published their datasets, and
every way a rule can fail to hold, which stops the run; the file R1 decided
says what it was decided on.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from uvlhub_splent.migration_v2 import curation
from uvlhub_splent.migration_v2.params import Refused


def dataset(dataset_id, created, origin=None, version=1, owner=1):
    return {
        "id": dataset_id,
        "user_id": owner,
        "ds_meta_data_id": 100 + dataset_id,
        "created_at": created,
        "dataset_origin_id": origin,
        "dataset_version": version,
    }


def meta(dataset_id, doi=None, deposition=None):
    doi = doi if doi is not None else f"10.5281/zenodo.{dataset_id}"
    return {
        "id": 100 + dataset_id,
        "dataset_doi": doi,
        "deposition_id": deposition if deposition is not None else dataset_id,
        "metadata_synced": 1,
        "dataset_anonymous": 0,
    }


def snapshot(deposition_id, created):
    text = json.dumps(
        {
            "id": deposition_id,
            "doi": f"10.5281/zenodo.{deposition_id}",
            "created": created,
        }
    )
    return {
        "deposition_id": deposition_id,
        "record": text,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def ctx_for(tmp_path, text):
    path = tmp_path / "curation.toml"
    path.write_text("version = 1\n" + text)
    return SimpleNamespace(params=SimpleNamespace(curation=path), facts={})


def lineage(name, *ids, dois=None):
    dois = dois or {}
    members = ", ".join(
        f'{{ id = {i}, doi = "{dois.get(i, f"10.5281/zenodo.{i}")}" }}' for i in ids
    )
    return f'[[lineage]]\nname = "{name}"\nmembers = [{members}]\n'


# Two lineages of v2.12 (74 -> 81, and 94 -> 95), and the datasets published
# again apart from them (75, 87); 60 and 61 are drafts.
DAY = datetime(2026, 3, 1)


def source():
    datasets = [
        dataset(74, DAY.replace(day=5)),
        dataset(75, DAY.replace(day=25)),
        dataset(81, DAY.replace(month=6, day=24), origin=74, version=2),
        dataset(87, DAY.replace(month=7, day=26)),
        dataset(94, DAY.replace(month=8, day=13)),
        dataset(95, DAY.replace(month=8, day=14), origin=94, version=2),
        dataset(60, DAY),
        dataset(61, DAY),
    ]
    metas = {meta(d["id"])["id"]: meta(d["id"]) for d in datasets}
    for draft in (60, 61):
        metas[100 + draft].update(dataset_doi=None, deposition_id=None)
    return {d["id"]: d for d in datasets}, metas


def test_published_duplicates_become_versions_in_the_order_zenodo_published_them(
    tmp_path,
):
    chosen, metas = source()
    ctx = ctx_for(tmp_path, lineage("cms", 94, 87, 95) + lineage("sample", 74, 75, 81))

    curated, changes = curation.apply(ctx, chosen, metas, {})

    places = {
        i: (curated[i]["dataset_origin_id"], curated[i]["dataset_version"])
        for i in (87, 94, 95, 74, 75, 81)
    }
    assert places == {
        87: (None, 1),
        94: (87, 2),
        95: (94, 3),
        74: (None, 1),
        # 75 was published after 74: it goes between 74 and 81.
        75: (74, 2),
        81: (75, 3),
    }
    assert chosen[94]["dataset_origin_id"] is None  # the source's rows stay
    assert {c["dataset_id"]: c for c in changes}[94] == {
        "dataset_id": 94,
        "lineage": "cms",
        "old_origin_id": None,
        "old_version": 1,
        "origin_id": 87,
        "version": 2,
    }
    assert {c["dataset_id"] for c in changes} == {94, 95, 75, 81}
    assert ctx.facts["curation"]["lineages"][0] == {
        "name": "cms",
        "before": [[87, None, 1], [94, None, 1], [95, 94, 2]],
        "after": [[87, None, 1], [94, 87, 2], [95, 94, 3]],
    }


def test_zenodos_time_orders_them_before_the_hubs(tmp_path):
    chosen, metas = source()
    ctx = ctx_for(tmp_path, lineage("sample", 74, 75, 81))
    # Zenodo published 75 first, whatever v2.12's created_at says.
    snapshots = {75: snapshot(75, "2026-02-01T10:00:00+00:00")}

    curated, _changes = curation.apply(ctx, chosen, metas, snapshots)

    assert [
        (i, curated[i]["dataset_origin_id"], curated[i]["dataset_version"])
        for i in (75, 74, 81)
    ] == [(75, None, 1), (74, 75, 2), (81, 74, 3)]


def refusal(tmp_path, text, change=None):
    chosen, metas = source()
    if change:
        change(chosen, metas)
    with pytest.raises(Refused) as refused:
        curation.apply(ctx_for(tmp_path, text), chosen, metas, {})
    assert refused.value.stage == "E5"
    return refused.value.reasons


def test_a_rule_on_other_rows_than_the_sources_stops_the_run(tmp_path):
    assert refusal(
        tmp_path, lineage("cms", 87, 94, 95, dois={94: "10.5281/zenodo.1"})
    ) == ["RU-06 cms: dataset 94 is not 10.5281/zenodo.1"]
    assert refusal(tmp_path, lineage("cms", 87, 94, 95, 99)) == [
        "RU-06 cms: dataset 99 does not load"
    ]

    def withdrawn(_chosen, metas):
        metas[187].update(dataset_doi=None)

    # A dataset that lost its DOI is no longer the one the rule names.
    assert refusal(tmp_path, lineage("cms", 87, 94, 95), withdrawn) == [
        "RU-06 cms: dataset 87 is not 10.5281/zenodo.87"
    ]


def test_a_dataset_out_of_sync_is_published_still(tmp_path):
    chosen, metas = source()
    metas[187].update(metadata_synced=0)

    curated, _changes = curation.apply(
        ctx_for(tmp_path, lineage("cms", 87, 94, 95)), chosen, metas, {}
    )

    assert curated[94]["dataset_origin_id"] == 87


def test_a_lineage_keeps_every_version_and_one_owner(tmp_path):
    # 95 stands on 94: the lineage that names 94 and not 95 would branch.
    assert refusal(tmp_path, lineage("cms", 87, 94)) == [
        "RU-06 cms: dataset 95 is a version of 94 and the lineage does not name it"
    ]
    # 81 stands on 74, which the lineage does not name.
    assert refusal(tmp_path, lineage("sample", 75, 81)) == [
        "RU-06 sample: dataset 81 stands on 74, which the lineage does not name"
    ]

    def other_owner(chosen, _metas):
        chosen[87]["user_id"] = 2

    assert refusal(tmp_path, lineage("cms", 87, 94, 95), other_owner) == [
        "RU-06 cms: its datasets are of more than one account, and a lineage has "
        "one owner"
    ]


def test_drafts_and_reviews_are_listed_and_left_as_they_are(tmp_path):
    chosen, metas = source()
    text = (
        '[[draft]]\ndatasets = [60, 61]\nwhy = "twice"\n'
        "[[draft]]\ndatasets = [61]\nof = [87]\n"
        '[[review]]\ndatasets = [74, 75]\nwhy = "one title"\n'
    )
    ctx = ctx_for(tmp_path, text)

    curated, changes = curation.apply(ctx, chosen, metas, {})

    assert curated == chosen and changes == []
    assert ctx.facts["curation"]["drafts_that_duplicate"] == [
        {"datasets": [60, 61], "of": [], "why": "twice"},
        {"datasets": [61], "of": [87], "why": ""},
    ]
    assert ctx.facts["curation"]["manual_review"] == [
        {"datasets": [74, 75], "why": "one title"}
    ]
    assert refusal(tmp_path, "[[draft]]\ndatasets = [87]\n") == [
        "RU-06 draft: dataset 87 is published"
    ]


def test_no_curation_changes_nothing():
    chosen, metas = source()
    ctx = SimpleNamespace(params=SimpleNamespace(curation=None), facts={})

    assert curation.apply(ctx, chosen, metas, {}) == (chosen, [])
    assert ctx.facts["curation"]["lineages"] == []


@pytest.mark.parametrize(
    "text, error",
    [
        ("version = 2\n", "version 1"),
        (
            "version = 1\n" + lineage("a", 1, 2) + lineage("b", 2, 3),
            "dataset 2 is in a and in b",
        ),
        ("version = 1\n" + lineage("a", 1), "a lineage of one dataset"),
        ('version = 1\n[[lineage]]\nname = "a"\nmembers = [{ id = 1 }]\n', "a DOI"),
        ("version = 1\n[[draft]]\ndatasets = []\n", "a list of dataset ids"),
        ("version = 1\n[[review]]\ndatasets = [true]\n", "integers"),
        ("version = ", "Invalid"),
    ],
)
def test_a_file_that_does_not_say_what_it_should_is_refused(tmp_path, text, error):
    path = tmp_path / "curation.toml"
    path.write_text(text)

    with pytest.raises(ValueError, match=error):
        curation.load(path)


def test_the_curation_r1_decided():
    """The duplicates uvlhub.io published, as R1 found them (RU-06): five
    lineages, the drafts their owners may remove, and four pairs left for
    someone to decide."""
    decided = curation.load(curation.CURATION)

    assert {
        lineage.name: [i for i, _doi in lineage.members] for lineage in decided.lineages
    } == {
        "openhubs_spl": [*range(108, 117), 120],
        "cms_spl": [87, 94, 95, 96, 97, 104],
        "Sample SPLENT app": [74, 75, 81, 82, 99],
        "marketplace_spl": [88, 101, 102],
        "demo_spl": [89, 90, 91],
    }
    assert all(
        doi.startswith("10.5281/zenodo.")
        for lineage in decided.lineages
        for _i, doi in lineage.members
    )
    drafts = {i for listed in decided.drafts for i in listed.datasets}
    assert drafts == {107, 47, 65, 66, 67, 83, 84, 85, 86}
    assert [list(r.datasets) for r in decided.review] == [
        [45, 50],
        [1, 17],
        [4, 18],
        [12, 15],
    ]
    members = {i for lineage in decided.lineages for i, _doi in lineage.members}
    reviewed = {i for listed in decided.review for i in listed.datasets}
    assert not members & drafts and not members & reviewed
    assert Path(curation.CURATION).name == "curation.toml"
