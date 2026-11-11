"""The migrator's rules that need no database, and the ones it reproduces in
Core, against the feature code they mirror (§3.4: "reproduce its rule in
Core and test the equivalence against the service").

No database is touched: the services are given a repository that records
what they would write.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from itsdangerous import URLSafeTimedSerializer

from uvlhub.migration_v2 import rules

from . import synthetic

T0 = synthetic.T0


def feature_migration(package: str, name: str):
    """A migration script of an installed feature, loaded from its file (the
    versions folder is no package), without compiling it there."""
    spec = importlib.util.find_spec(package)
    script = (
        Path(spec.submodule_search_locations[0])
        / "migrations"
        / "versions"
        / f"{name}.py"
    )
    loader_spec = importlib.util.spec_from_file_location(f"_migration_{name}", script)
    module = importlib.util.module_from_spec(loader_spec)
    writes, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        loader_spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = writes
    return module


# ── ORCID ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value, expected",
    [
        ("0000-0002-1694-233X", "0000-0002-1694-233X"),
        ("0000-0002-1694-233x", "0000-0002-1694-233X"),
        (" https://orcid.org/0000-0002-1694-233X ", "0000-0002-1694-233X"),
        ("000000021694233X", "0000-0002-1694-233X"),
        ("0000-0002-1694-2331", None),
        ("0000-0000-0000-0000", None),
        ("not an iD", None),
        ("", None),
        (None, None),
    ],
)
def test_an_orcid_is_normalised_or_refused(value, expected):
    assert rules.normalize_orcid(value) == expected


# ── Reset links (P-26) ───────────────────────────────────────────────────


def test_a_reset_link_is_read_without_its_key():
    link = URLSafeTimedSerializer("whatever v2.12 had").dumps(
        "josé@uvlhub.test", salt="email-confirm"
    )
    typed, issued = rules.decode_reset_token(link)
    assert typed == "josé@uvlhub.test"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs(issued - now) < timedelta(minutes=1)


def test_a_compressed_reset_link_is_read_too():
    address = "a" * 80 + "@uvlhub.test"
    link = synthetic.reset_link(address)
    assert link.startswith(".")
    assert rules.decode_reset_token(link) == (address, datetime(2026, 1, 15))


@pytest.mark.parametrize(
    "token", ["", "garbage", "a.b.c", "not-a-link-of-v2.12", "...."]
)
def test_what_is_not_a_reset_link_reads_as_nothing(token):
    assert rules.decode_reset_token(token) == (None, None)


@pytest.mark.parametrize(
    "typed, account, matches",
    [
        ("alice@uvlhub.test", "alice@uvlhub.test", True),
        (" Alice@UVLHUB.test ", "alice@uvlhub.test", True),
        ("josé@uvlhub.test", "jose@uvlhub.test", False),
        ("ﬁle@uvlhub.test", "file@uvlhub.test", False),
    ],
)
def test_a_reset_link_proves_only_the_address_it_went_to(typed, account, matches):
    assert rules.reset_matches_account(typed, account) is matches


# ── Legacy proofs: record_legacy_proof ───────────────────────────────────


@pytest.mark.parametrize(
    "proofs",
    [
        [],
        [(rules.LEGACY_RESET, datetime(2025, 5, 1))],
        [
            (rules.LEGACY_RESET, datetime(2025, 5, 1)),
            (rules.LEGACY_GITHUB, datetime(2025, 1, 2)),
        ],
        [
            (rules.LEGACY_GITHUB, datetime(2025, 9, 9)),
            (rules.LEGACY_RESET, datetime(2025, 9, 1)),
            (rules.LEGACY_RESET, datetime(2026, 1, 1)),
        ],
    ],
)
def test_legacy_proof_is_what_record_legacy_proof_records(proofs):
    """The proofs given to auth's service in the order they happened leave
    the account as the migrator's rule writes it."""
    from splent_io.splent_feature_auth.models import ORIGIN_LEGACY, User
    from splent_io.splent_feature_auth.services import AuthenticationService

    user = User(
        email="a@uvlhub.test",
        has_usable_password=False,
        email_verified_at=None,
        account_origin=ORIGIN_LEGACY,
    )
    service = AuthenticationService()
    service.repository = SimpleNamespace(
        session=SimpleNamespace(
            flush=lambda: None, commit=lambda: None, rollback=lambda: None
        )
    )
    for via, at in sorted(proofs, key=lambda proof: proof[1]):
        service.record_legacy_proof(user, via, at, commit=False)
    assert rules.legacy_proof(proofs) == (
        user.email_verified_via,
        user.email_verified_at,
    )


def test_the_proofs_the_migrator_writes_are_the_ones_auth_knows():
    from splent_io.splent_feature_auth.models import LEGACY_PROOFS

    assert {rules.LEGACY_RESET, rules.LEGACY_GITHUB} == set(LEGACY_PROOFS)


@pytest.mark.parametrize(
    "identity_seconds, reset_followed, usable",
    [
        (2, False, False),
        (5, False, False),
        (6, False, True),
        (2, True, True),
        (None, False, True),
    ],
)
def test_an_account_opened_through_a_provider_has_no_usable_password(
    identity_seconds, reset_followed, usable
):
    created = datetime(2025, 1, 10, 10, 0, 0)
    dates = (
        []
        if identity_seconds is None
        else [created + timedelta(seconds=identity_seconds)]
    )
    assert rules.has_usable_password(created, dates, reset_followed) is usable


# ── API keys (D12) ───────────────────────────────────────────────────────


def test_an_aware_date_is_written_as_naive_utc():
    from datetime import timezone as tz

    aware = datetime(2026, 11, 20, 1, 0, tzinfo=tz(timedelta(hours=1)))
    assert rules.naive_utc(aware) == datetime(2026, 11, 20, 0, 0)
    assert rules.naive_utc(datetime(2026, 11, 20)) == datetime(2026, 11, 20)
    assert rules.naive_utc(None) is None and rules.naive_utc("x") == "x"


def test_scopes_go_through_the_contract():
    vocabulary = {"read_dataset": "read_dataset", "write_dataset": "write_dataset"}
    assert rules.translate_scopes(
        "read_dataset, write_dataset,read_dataset,magic", vocabulary
    ) == (
        ["read_dataset", "write_dataset"],
        ["magic"],
    )
    assert rules.translate_scopes("", vocabulary) == ([], [])


# ── Identities: orcid0002, github0002, identities0002 ────────────────────


FOLD_CASES = {
    "orcid": (
        [
            (1, "0000-0002-1694-233X", "0000-0002-1694-233X", datetime(2025, 2, 1), 1),
            (6, "0000-0002-7777-7778", "0000-0002-7777-7778", datetime(2025, 6, 1), 3),
        ],
        [(1, 1, "0000-0002-1694-233X", None, datetime(2025, 3, 1))],
    ),
    "github": (
        [
            (1, "1001", "bobgh", datetime(2025, 1, 10, 10, 0, 1), 2),
            (2, "2001", "erin-gh", datetime(2025, 8, 1), 14),
        ],
        [(2, 2, "1001", "bobgh", datetime(2025, 1, 10, 10, 0, 2))],
    ),
}


@pytest.mark.parametrize("provider", ["orcid", "github"])
def test_folding_a_provider_table_is_what_its_feature_does(provider):
    """Without conflicts, the fold adds and completes exactly what the
    provider feature's own migration does."""
    module = feature_migration(
        f"splent_io.splent_feature_{provider}",
        "orcid0002_into_external_identity"
        if provider == "orcid"
        else "github0002_into_ext_identity",
    )
    legacy, existing = FOLD_CASES[provider]
    mine = rules.fold_identities(provider, legacy, existing)
    if provider == "orcid":
        theirs = module.plan([(r, p, d, u) for r, p, _n, d, u in legacy], existing)
    else:
        theirs = module.plan(
            [(r, int(p), n, d, u) for r, p, n, d, u in legacy], existing
        )
    assert mine == theirs


@pytest.mark.parametrize(
    "legacy, existing, kind",
    [
        (
            [(3, "X", "X", datetime(2025, 1, 1), 14)],
            [(4, 12, "X", "X", datetime(2025, 1, 1))],
            "other_account",
        ),
        (
            [(2, "Y", "Y", datetime(2025, 1, 1), 12)],
            [(4, 12, "X", "X", datetime(2025, 1, 1))],
            "second_identity",
        ),
        ([(4, "Z", "Z", datetime(2025, 1, 1), None)], [], rules.FOLD_ORPHAN),
    ],
)
def test_what_orcid0002_refuses_is_a_conflict_here(legacy, existing, kind):
    module = feature_migration(
        "splent_io.splent_feature_orcid", "orcid0002_into_external_identity"
    )
    _inserts, _updates, conflicts = rules.fold_identities("orcid", legacy, existing)
    _i, _u, refused = module.plan([(r, p, d, u) for r, p, _n, d, u in legacy], existing)
    assert [c[1] for c in conflicts] == [kind]
    assert len(refused) == 1


def test_provider_email_verified_is_what_identities0002_keeps():
    module = feature_migration(
        "splent_io.splent_feature_identities", "identities0002_one_per_provider"
    )
    rows = [
        (1, "bob@uvlhub.test", "bob@uvlhub.test"),
        (2, "Bob@UVLhub.test ", "bob@uvlhub.test"),
        (3, "other@uvlhub.test", "bob@uvlhub.test"),
        (4, None, "bob@uvlhub.test"),
        (5, "bob@uvlhub.test", None),
    ]
    theirs = dict(module.proofs(rows))
    mine = {
        identity_id: rules.provider_email_verified(
            "github", provider_email, account_email
        )
        for identity_id, provider_email, account_email in rows
    }
    assert {k: v for k, v in mine.items() if v is not None} == theirs
    assert (
        rules.provider_email_verified("orcid", "bob@uvlhub.test", "bob@uvlhub.test")
        is None
    )


# ── Ids and lineages (§4.1) ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "counter, max_id, expected",
    [
        (None, None, 10000),
        (40, 15, 10000),
        (9500, 9400, 20000),
        (8999, 8000, 10000),
        (8999, 9001, 20000),
    ],
)
def test_the_counter_of_3_0_has_its_margin(counter, max_id, expected):
    assert rules.next_counter(counter, max_id, 1000, 10000) == expected


def test_a_lineage_root_is_found_and_a_cycle_ends_the_walk():
    assert rules.lineage_root(3, {1: None, 2: 1, 3: 2}) == 1
    assert rules.lineage_root(1, {1: 2, 2: 1}) == 2


@pytest.mark.parametrize(
    "doi, zenodo",
    [
        ("10.5281/zenodo.1", True),
        ("10.5072/zenodo.55", False),
        ("10.1234/dataset1", False),
        (None, False),
    ],
)
def test_only_zenodo_production_dois_are_zenodo(doi, zenodo):
    assert rules.doi_is_zenodo(doi) is zenodo


@pytest.mark.parametrize(
    "doi, deposition, its",
    [
        ("10.5281/zenodo.1011", 1011, True),
        (" 10.5281/zenodo.1011", 1011, True),
        ("10.5281/zenodo.1011", 1012, False),
        ("10.5281/zenodo.1011", None, False),
        ("10.5072/zenodo.55", 55, False),
    ],
)
def test_a_doi_is_its_depositions_only_as_zenodo_mints_it(doi, deposition, its):
    assert rules.doi_is_of_deposition(doi, deposition) is its


@pytest.mark.parametrize(
    "value, signed",
    [
        (synthetic.reset_link("alice@uvlhub.test"), True),
        # Long enough for itsdangerous to compress it.
        (synthetic.reset_link("a" * 80 + "@uvlhub.test"), True),
        ("J.R.R", False),
        ("10.5281/zenodo.1001", False),
        ("alice@uvlhub.test", False),
        ("a.b.c", False),
        ("uvlhub 2 key (2026-01-01)", False),
        (None, False),
    ],
)
def test_dm1_knows_a_signed_value_without_its_key(value, signed):
    assert rules.is_signed(value) is signed


# ── Content (§4.3, §7.3, §8) ─────────────────────────────────────────────


def kept(record) -> dict:
    """A row of zenodo_snapshot keeping ``record``."""
    text = json.dumps(record, sort_keys=True)
    return {"record": text, "sha256": synthetic.sha256(text.encode("utf-8"))}


MINTED = {
    "id": 2005,
    "doi": "10.5281/zenodo.2005",
    "status": "published",
    "metadata": {"title": "Deleted,  minted "},
}


@pytest.mark.parametrize(
    "snapshot, deposition, title, why",
    [
        (kept(MINTED), 2005, "Deleted, minted", None),
        (None, 2005, "Deleted, minted", None),
        (kept(MINTED), 2006, "Deleted, minted", "not 2006"),
        (kept(MINTED), 2005, "Another title", "another title"),
        (kept(dict(MINTED, status="draft")), 2005, "Deleted, minted", "draft"),
        (kept(dict(MINTED, doi="")), 2005, "Deleted, minted", "no DOI"),
        (
            dict(kept(MINTED), sha256="0" * 64),
            2005,
            "Deleted, minted",
            "sha256",
        ),
    ],
)
def test_a_deposition_without_a_doi_takes_the_one_its_record_has(
    snapshot, deposition, title, why
):
    """A15-04: Zenodo published it and v2.12 lost the DOI; the record is
    taken on its id, its state, its DOI and its title, word for word. No
    record at all is no conflict: Zenodo never published it."""
    record, reason = rules.minted_record(snapshot, deposition, title)
    if why is None and snapshot is not None:
        assert record["doi"] == "10.5281/zenodo.2005" and reason is None
    elif why is None:
        assert (record, reason) == (None, None)
    else:
        assert record is None and why in reason


@pytest.mark.parametrize(
    "html, tags, active",
    [
        ("<p>About <strong>it</strong></p>", {"p", "strong"}, ()),
        ("<p>x</p><script>alert(1)</script>", {"p", "script"}, ("<script>",)),
        ('<img src="x" onerror="alert(1)">', {"img"}, ("onerror=",)),
        ('<a href="jav&#x61;script:alert(1)">x</a>', {"a"}, ("href=javascript:",)),
        ('<a href=" java\tscript:alert(1)">x</a>', {"a"}, ("href=javascript:",)),
        ('<a href="https://uvlhub.io/x:y">x</a>', {"a"}, ()),
        ('<span style="color:red">x</span>', {"span"}, ()),
        ("", set(), ()),
        (None, set(), ()),
    ],
)
def test_a_description_s_markup_and_what_in_it_runs(html, tags, active):
    """C-01: the elements a description uses (P-22's frequency) and the
    plan's second class, active content, which a curator reads."""
    found = rules.markup(html)
    assert found.tags == tags and found.active == active


@pytest.mark.parametrize(
    "value, expected",
    [
        ("https://doi.org/10.1145/3646548.3672589", "10.1145/3646548.3672589"),
        ("http://dx.doi.org/10.1145/x", "10.1145/x"),
        ("doi: 10.1145/x", "10.1145/x"),
        (" 10.1145/x ", "10.1145/x"),
        # Not a DOI (a registrant has four digits or more), and no address.
        ("10.1/x", "10.1/x"),
        ("  https://example.org/paper ", "https://example.org/paper"),
        ("in press", "in press"),
        ("", ""),
        ("   ", ""),
        (None, None),
    ],
)
def test_a_publication_doi_is_bare_as_dataset_keeps_it(value, expected):
    """C-16, with dataset's own publication_doi_of; what is no DOI and no
    address stays as it was, for its owner to mend."""
    assert rules.publication_doi(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("uvl, models", "uvl,models"),
        ("uvl, models, uvl, ", "uvl,models"),
        (" Feature  Models ,UVL,uvl", "Feature Models,UVL,uvl"),
        (",,", ""),
        ("", ""),
        (None, None),
    ],
)
def test_the_tags_are_split_trimmed_and_said_once(value, expected):
    """C-23, a string still: each tag once, its spelling kept (UVL and uvl
    are two, as utf8mb4_bin has them), joined as dataset joins them."""
    assert rules.normal_tags(value) == expected


def test_v2_12_s_metrics_are_stale_for_factlabel():
    """§7.3: status = 'legacy', in factlabel's terms: any version but its
    EXTRACTOR_VERSION is one metrics-backfill extracts again."""
    from splent_io.splent_feature_factlabel.metrics_extraction import (
        EXTRACTOR_VERSION,
    )

    assert rules.legacy_extractor_version("1", 20) == "legacy:1"
    assert rules.legacy_extractor_version("1", 20) != EXTRACTOR_VERSION
    assert rules.legacy_extractor_version("x" * 30, 20) == "legacy:" + "x" * 13
    assert rules.legacy_extractor_version(None, 20) == "legacy:"


def version(dataset_id, day, number, origin=None):
    return {
        "id": dataset_id,
        "created_at": datetime(2026, 1, day),
        "dataset_version": number,
        "dataset_origin_id": origin,
    }


def test_a_concept_doi_makes_its_datasets_one_lineage_by_date():
    """C-05: by created_at, each on the one before, the versions as they
    are; the first keeps an origin outside the concept."""
    members = [
        version(14, 3, 3, origin=1),
        version(2, 2, 2, origin=1),
        version(1, 1, 1),
    ]
    assert rules.concept_chain(members) == [(1, None), (2, 1), (14, 2)]
    # A gap stays a gap: dataset_version is never renumbered.
    assert rules.concept_chain([version(7, 1, 2, origin=5), version(8, 2, 4)]) == [
        (7, 5),
        (8, 7),
    ]


def test_a_first_version_standing_on_a_later_one_is_the_root():
    assert rules.concept_chain([version(1, 1, 1, origin=2), version(2, 2, 2)]) == [
        (1, None),
        (2, 1),
    ]


@pytest.mark.parametrize(
    "members",
    [
        # Two versions 2: only renumbering would make a lineage of them.
        [version(1, 1, 1), version(2, 2, 2, origin=1), version(14, 3, 2, origin=1)],
        # A version made before the one it follows.
        [version(1, 2, 1), version(2, 1, 2, origin=1)],
    ],
)
def test_a_lineage_the_dates_and_versions_do_not_agree_on_is_left(members):
    """Left to a decision, the curation's (RU-06), and to V-09."""
    assert rules.concept_chain(members) is None
