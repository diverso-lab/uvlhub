"""E5's own steps that need no database, given what they read as rows.

The rehearsal (test_pipeline) runs them on the synthetic source; here each
one meets the cases the source does not have: a source at the hotfix's
head with B0 and without it, and a lineage the curation made.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from uvlhub.migration_v2 import content
from uvlhub.migration_v2.ledger import Ledger

ORIGINAL = '<p>Hi <a href="https://uvlhub.io" target="_blank">there</a></p><script>x()</script>'
# What the hotfix D1 (bleach, strip=True) left of it.
HOTFIXED = '<p>Hi <a href="https://uvlhub.io" target="_blank">there</a></p>x()'


def ctx_for(head="e5f6a7b8c9d0", b0=None, facts=None):
    return SimpleNamespace(
        params=SimpleNamespace(expected_head=head),
        b0=b0,
        alerts=[],
        facts=facts or {},
        ledger=Ledger(),
    )


def described(ctx, text):
    metas = {201: {"id": 201, "description": text}}
    rows = [{"id": 201, "description": text}]
    return content.describe(ctx, rows, metas), rows[0]


def test_a_description_is_cleaned_again_and_its_original_quarantined():
    """C-01: before the hotfix the source is the original."""
    ctx = ctx_for()
    quarantine, row = described(ctx, ORIGINAL)
    assert row["description_format"] == "html_legacy"
    assert row["description"] == (
        '<p>Hi <a href="https://uvlhub.io" rel="nofollow ugc noopener">there</a></p>'
    )
    assert quarantine == [
        {"ds_meta_data_id": 201, "original": ORIGINAL, "sanitized": row["description"]}
    ]
    facts = ctx.facts["descriptions"]
    assert facts["originals"] == "source" and facts["active_content"] == [201]
    assert facts["elements"] == {"a": 1, "p": 1, "script": 1}
    assert ctx.alerts == []


def test_after_the_hotfix_the_original_is_b0s():
    """C-29: what v2.12 has now is cleaned again (what uvlhub.io shows stays),
    and the original the hotfix rewrote comes from B0."""
    ctx = ctx_for(head=content.HOTFIX_HEAD, b0={201: ORIGINAL})
    quarantine, row = described(ctx, HOTFIXED)
    assert row["description"].endswith("</p>x()")
    assert quarantine[0]["original"] == ORIGINAL
    facts = ctx.facts["descriptions"]
    assert facts["originals"] == "b0" and facts["b0_differs"] == [201]
    assert facts["active_content"] == [201]


def test_after_the_hotfix_without_b0_the_loss_is_said():
    ctx = ctx_for(head=content.HOTFIX_HEAD)
    quarantine, row = described(ctx, HOTFIXED)
    assert quarantine[0]["original"] == HOTFIXED
    assert ctx.facts["descriptions"]["originals"] == "lost"
    assert ctx.facts["descriptions"]["active_content"] == []
    assert len(ctx.alerts) == 1 and ctx.alerts[0].startswith("C-29")


def test_a_clean_description_is_not_quarantined():
    ctx = ctx_for()
    quarantine, row = described(ctx, "<p>Clean</p>")
    assert quarantine == [] and row["description"] == "<p>Clean</p>"
    assert ctx.ledger.notes == {}


def dataset(dataset_id, day, version, origin=None):
    return {
        "id": dataset_id,
        "ds_meta_data_id": 100 + dataset_id,
        "created_at": datetime(2026, 1, day),
        "dataset_version": version,
        "dataset_origin_id": origin,
    }


def meta(dataset_id, concept=None):
    return {"id": 100 + dataset_id, "dataset_concept_doi": concept}


def test_the_concept_doi_repairs_a_branch_but_not_the_curations_lineage():
    """C-05: 2 and 3 both stand on 1 and share its concept, Zenodo's for 3;
    4 and 5 share another, but the curation made them a lineage (RU-06),
    which stays as it is."""
    chosen = {
        1: dataset(1, 1, 1),
        2: dataset(2, 2, 2, origin=1),
        3: dataset(3, 3, 3, origin=1),
        4: dataset(4, 4, 1),
        5: dataset(5, 5, 1),
    }
    metas = {
        101: meta(1, "10.5281/zenodo.100"),
        102: meta(2, "10.5281/zenodo.100"),
        103: meta(3),
        104: meta(4, "10.5281/zenodo.400"),
        105: meta(5, "10.5281/zenodo.400"),
    }
    curation = {"lineages": [{"name": "x", "after": [[4, None, 1], [5, 4, 2]]}]}
    ctx = ctx_for(facts={"curation": curation})
    repaired, changes = content.repair_lineages(
        ctx, chosen, metas, {103: "10.5281/zenodo.100"}
    )
    assert repaired[3]["dataset_origin_id"] == 2
    assert repaired[2] is chosen[2] and repaired[4] is chosen[4]
    assert changes == [
        {
            "dataset_id": 3,
            "lineage": "C-05 10.5281/zenodo.100",
            "old_origin_id": 1,
            "old_version": 3,
            "origin_id": 2,
            "version": 3,
        }
    ]
    assert ctx.facts["lineages_by_concept"] == {
        "repaired": [
            {"concept": "10.5281/zenodo.100", "chain": [[1, None], [2, 1], [3, 2]]}
        ],
        "left": [],
    }


def test_a_concept_whose_versions_do_not_rise_is_left_for_a_decision():
    chosen = {1: dataset(1, 1, 1), 2: dataset(2, 2, 2, 1), 3: dataset(3, 3, 2, 1)}
    metas = {100 + i: meta(i, "10.5281/zenodo.100") for i in chosen}
    ctx = ctx_for(facts={})
    repaired, changes = content.repair_lineages(ctx, chosen, metas, {})
    assert repaired == chosen and changes == []
    assert ctx.facts["lineages_by_concept"]["left"] == [
        {
            "concept": "10.5281/zenodo.100",
            "datasets": [1, 2, 3],
            "why": "its versions do not rise with their created_at",
        }
    ]


def test_a_lineage_that_is_one_line_already_is_left_as_it_is():
    """Its versions stand on one another, though 2 was made before 1: there
    is nothing to repair, and nothing is said."""
    chosen = {1: dataset(1, 2, 1), 2: dataset(2, 1, 2, 1), 3: dataset(3, 3, 3, 2)}
    metas = {100 + i: meta(i, "10.5281/zenodo.100") for i in chosen}
    ctx = ctx_for(facts={})
    repaired, changes = content.repair_lineages(ctx, chosen, metas, {})
    assert repaired == chosen and changes == []
    assert ctx.facts["lineages_by_concept"] == {"repaired": [], "left": []}
