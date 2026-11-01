"""The rules of the migration that need no database: each one a function the
tests call directly.

The domain rules belong to the pinned features and are imported from them
(principle 4): auth's canonical_email, dataset's state_from_metadata and
publication_doi_of, hubfile's checksum_algorithm, apikeys'
imported_token_fields (the row ApiTokenService.import_token stores,
without a session). One lives in an
ORM service only, and the migrator writes with Core, so it is reproduced
here, and tests/migration_v2/test_rules.py checks that both answer the
same: legacy_proof (AuthenticationService.record_legacy_proof). The fold
of the orcid and github tables mirrors those features' own migrations
(orcid0002, github0002), which refuse what the migrator records as a
conflict.
"""

from __future__ import annotations

import hashlib
import json
import re
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser

from itsdangerous.encoding import base64_decode
from itsdangerous.exc import BadData
from splent_io.splent_feature_dataset.creation import publication_doi_of

# ── Accounts (§5.1, §5.2) ────────────────────────────────────────────────

# The seed of v2.12 (mono/app/features/auth/seeders.py) and anything that
# looks like it (P-25): never loaded, and reviewed.
SEED_EMAIL_SUFFIX = "@example.com"

# §5.2: an account opened by ORCID or GitHub was given a random password
# within moments of its identity.
PROVIDER_ACCOUNT_SECONDS = 5

LEGACY_RESET = "legacy_reset"
LEGACY_GITHUB = "legacy_github"


def is_seed_email(email) -> bool:
    return bool(email) and email.strip().lower().endswith(SEED_EMAIL_SUFFIX)


def _signed(token):
    """(payload, issued at) of a value itsdangerous' URLSafeTimedSerializer
    signed, read without its key, or None for anything else.

    Such a value is the payload, the time and the signature, joined by
    dots. The payload is base64url JSON, zlib-compressed when it starts with
    a dot; the time is a big-endian integer of seconds, in base64url too.
    """
    try:
        value, stamp, _signature = token.rsplit(".", 2)
        compressed = value.startswith(".")
        data = base64_decode(value[1:] if compressed else value)
        if compressed:
            data = zlib.decompress(data)
        payload = json.loads(data)
        seconds = int.from_bytes(base64_decode(stamp), "big")
        issued = datetime.fromtimestamp(seconds, timezone.utc).replace(tzinfo=None)
    except (
        AttributeError,
        BadData,
        ValueError,
        TypeError,
        zlib.error,
        OverflowError,
        OSError,
    ):
        return None
    return payload, issued


def decode_reset_token(token: str):
    """(address, issued at) a reset link of v2.12 carries, read without its
    key (P-26), or (None, None) for one that is not such a link: v2.12
    signed the address the reset form was given."""
    found = _signed(token)
    if found is None or not isinstance(found[0], str):
        return None, None
    return found


def is_signed(value) -> bool:
    """DM-1: whether ``value`` is something itsdangerous signed with a key,
    v2.12's or any other: a reset link, a confirmation link, a session. The
    rotated SECRET_KEY opens none of them, so none is carried over."""
    return isinstance(value, str) and _signed(value) is not None


def reset_matches_account(typed: str, account_email: str) -> bool:
    """Whether a reset link went to the account's own address (P-26).

    v2.12 found the account with typed.strip().lower() under the database's
    collation, which ignores accents, so "josé@" opened the account of
    "jose@" and mailed the link to "josé@". Byte for byte, after the same
    lowering, is the only match that proves the account's mailbox got it.
    """
    return typed.strip().lower() == (account_email or "").lower()


def legacy_proof(proofs):
    """(via, at) of the proof that confirms a carried-over address, or
    (None, None) without one.

    ``proofs`` are (via, at) pairs, in any order. The earliest wins:
    record_legacy_proof keeps the first proof an address gets, and given
    them in the order they happened, that is the earliest.
    """
    dated = sorted((at, via) for via, at in proofs if at is not None)
    if not dated:
        return None, None
    at, via = dated[0]
    return via, at


def has_usable_password(created_at, identity_dates, reset_followed: bool) -> bool:
    """§5.2: False for an account opened through a provider, whose password
    nobody knows. That is an account created within
    PROVIDER_ACCOUNT_SECONDS of one of its identities and whose owner never
    followed a reset link; any other account set a password of its own."""
    if reset_followed or created_at is None:
        return True
    for date in identity_dates:
        if date is not None and abs((date - created_at).total_seconds()) <= (
            PROVIDER_ACCOUNT_SECONDS
        ):
            return False
    return True


# ── ORCID (§5.6, C-15) ───────────────────────────────────────────────────

_ORCID = re.compile(r"^(\d{4})-?(\d{4})-?(\d{4})-?(\d{3}[\dX])$")
_ORCID_PREFIXES = ("HTTPS://ORCID.ORG/", "HTTP://ORCID.ORG/", "ORCID.ORG/")


def orcid_check_digit(digits: str) -> str:
    """ISO 7064 11,2 over the first 15 digits of an iD."""
    total = 0
    for digit in digits:
        total = (total + int(digit)) * 2
    result = (12 - total % 11) % 11
    return "X" if result == 10 else str(result)


def normalize_orcid(value) -> str | None:
    """An iD as 0000-0000-0000-000X, X in capitals, or None when it is not
    a valid one (its check digit is wrong, or it is not an iD at all)."""
    text = (value or "").strip().upper()
    for prefix in _ORCID_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :]
    match = _ORCID.match(text)
    if not match:
        return None
    digits = "".join(match.groups())
    if orcid_check_digit(digits[:15]) != digits[15]:
        return None
    return "-".join(match.groups())


# ── Identities (§5.6, ID-11) ─────────────────────────────────────────────

# The kind of conflict fold_identities gives a row that belongs to no
# account, which the migrator drops instead (§5.6, step 2).
FOLD_ORPHAN = "orphan"


def fold_identities(provider: str, legacy, existing):
    """What folding a provider table of v2.12 (orcid or github) into
    external_identity takes: (inserts, updates, conflicts).

    ``legacy`` holds (row id, provider id, username, date, user id or None)
    of every row of the table, the provider id already normalised;
    ``existing`` (identity id, user id, provider id, username, date) of
    every identity of ``provider`` already in external_identity. As
    orcid0002 and github0002 do: an identity that is already the account's
    stays, with the earlier date and the username it lacked; one that is
    not there is added; one that is another account's, or an account that
    already has another identity of the provider, is a conflict. Here a
    conflict is returned as (row id, kind, detail) and the rest goes on.
    Python compares the ids byte for byte, the BINARY of §5.6.
    """
    by_id = {str(row[2]): row for row in existing}
    by_user = {row[1]: row for row in existing}
    inserts, updates, conflicts = [], [], []
    for row_id, provider_id, username, date, user_id in legacy:
        if user_id is None:
            conflicts.append(
                (row_id, FOLD_ORPHAN, f"{provider} row belongs to no account")
            )
            continue
        linked = by_id.get(provider_id)
        if linked is not None:
            identity_id, linked_user, _id, linked_username, created = linked
            if linked_user != user_id:
                conflicts.append(
                    (
                        row_id,
                        "other_account",
                        f"{provider_id} is user {user_id}'s here and user "
                        f"{linked_user}'s in external_identity",
                    )
                )
                continue
            values = {}
            if not linked_username and username:
                values["provider_username"] = username
            if date is not None and (created is None or date < created):
                values["created_at"] = date
            if values and identity_id is not None:
                updates.append((identity_id, values))
            continue
        other = by_user.get(user_id)
        if other is not None:
            conflicts.append(
                (
                    row_id,
                    "second_identity",
                    f"user {user_id} has {provider_id} here and {other[2]} in "
                    "external_identity",
                )
            )
            continue
        inserts.append(
            {
                "user_id": user_id,
                "provider": provider,
                "provider_id": provider_id,
                "provider_username": username,
                "created_at": date,
            }
        )
        by_id[provider_id] = (None, user_id, provider_id, username, date)
        by_user[user_id] = by_id[provider_id]
    return inserts, updates, conflicts


def provider_email_verified(provider: str, provider_email, account_email):
    """What identities0002 keeps of an identity's address: a GitHub one that
    is the account's own, compared without case. ORCID verifies nothing."""
    if provider != "github" or not provider_email or not account_email:
        return None
    if provider_email.strip().lower() != account_email.strip().lower():
        return None
    return provider_email


# ── API keys (§5.5, D12) ─────────────────────────────────────────────────


def translate_scopes(scopes: str, vocabulary: dict[str, str]):
    """(scopes the token keeps, scopes that went): the key's comma separated
    names through the contract's [scopes], in their order, once each."""
    kept, gone = [], []
    for name in (scopes or "").split(","):
        name = name.strip()
        if not name:
            continue
        target = vocabulary.get(name)
        if target is None:
            gone.append(name)
        elif target not in kept:
            kept.append(target)
    return kept, gone


def naive_utc(value):
    """A date as the DATETIME columns hold it: UTC without its zone. What is
    not an aware date is given back as it is."""
    if isinstance(value, datetime) and value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


# ── Datasets (§4.1, §4.3) ────────────────────────────────────────────────


def next_counter(source_counter, max_id, margin: int, rounding: int) -> int:
    """C3 of §4.1: the AUTO_INCREMENT 3.0 starts a table at.

    The larger of the source's counter and max(id) + 1, so the id of a row
    deleted last is never handed out again, plus the margin, so a v2.12
    restored after writes opened (RB-2) cannot hand out an id 3.0 already
    gave, rounded up to the next ``rounding``.
    """
    start = max(source_counter or 1, (max_id or 0) + 1)
    return -(-(start + margin) // rounding) * rounding


def lineage_root(dataset_id, origins: dict) -> int:
    """The first version of a dataset's lineage: dataset_origin_id followed
    up, in ``origins`` (id -> origin id), stopping at a cycle."""
    seen = {dataset_id}
    node = dataset_id
    while origins.get(node) is not None and origins[node] not in seen:
        node = origins[node]
        seen.add(node)
    return node


def doi_is_zenodo(doi) -> bool:
    """C-30: a DOI of Zenodo's production (10.5281). 10.5072 is the sandbox's
    and anything else is not Zenodo's at all."""
    return bool(doi) and doi.strip().startswith("10.5281/")


def doi_is_of_deposition(doi, deposition_id) -> bool:
    """C-30: the DOI Zenodo mints for the deposition, 10.5281/zenodo.<id>.
    Any other is someone else's record, or a deposition_id of the sandbox
    that names one in production (P-25)."""
    return deposition_id is not None and (doi or "").strip() == (
        f"10.5281/zenodo.{deposition_id}"
    )


def suffixed_name(name: str, hubfile_id: int, limit: int) -> str:
    """DM-10 (C-11): ``name`` with ~<id> before its extension, so a second
    file on one path gets a path of its own and keeps its type; the stem is
    cut short when the whole would not fit in ``limit`` characters."""
    stem, dot, extension = name.rpartition(".")
    if not dot or not stem:
        stem, extension = name, ""
    suffix = f"~{hubfile_id}" + (f".{extension}" if extension else "")
    return stem[: max(limit - len(suffix), 1)] + suffix


def _kept_record(snapshot):
    """The record a row of uvlhub_migration_inputs.zenodo_snapshot keeps, as
    JSON, or None when there is no row or its sha256 is not its text's."""
    if snapshot is None:
        return None
    text = snapshot["record"] or ""
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != snapshot["sha256"]:
        return None
    try:
        record = json.loads(text)
    except ValueError:
        return None
    return record if isinstance(record, dict) else None


def zenodo_record(snapshot, doi):
    """A dataset's record in zenodo_snapshot, as JSON, or None when there is
    no record or it does not validate: its sha256 is not the snapshot's, or
    its DOI is not ``doi`` (§4.3, compared without case or surrounding
    spaces). ``snapshot`` is the row of
    uvlhub_migration_inputs.zenodo_snapshot, or None."""
    record = _kept_record(snapshot)
    if record is None or (record.get("doi") or "").strip().lower() != (
        (doi or "").strip().lower()
    ):
        return None
    return record


def _words(text) -> str:
    return " ".join(str(text or "").split())


def minted_record(snapshot, deposition_id, title):
    """§4.3, A15-04 (C-09): (record, None) when the record zenodo_snapshot
    keeps of a deposition v2.12 saved no DOI for shows that Zenodo
    published it all the same, else (None, why).

    Without a DOI there is nothing to compare, so the plan takes the record
    on its id and its title: it is the deposition's (its id), it is
    published, it has a DOI, and its title is the metadata's (compared
    word for word, whatever the spaces). A deposition id that names a record
    of somebody else (a sandbox's, P-25) fails on the title. With no row in
    the snapshot at all, the public API answered 404: Zenodo never
    published it, and it is (None, None)."""
    if snapshot is None:
        return None, None
    record = _kept_record(snapshot)
    if record is None:
        return None, "its record in zenodo_snapshot is not the text kept (sha256)"
    if str(record.get("id")) != str(deposition_id):
        return None, f"the record kept is {record.get('id')}, not {deposition_id}"
    if (record.get("status") or "published") != "published":
        return None, f"Zenodo's record is {record.get('status')}, not published"
    if not (record.get("doi") or "").strip():
        return None, "Zenodo's record has no DOI"
    found = (record.get("metadata") or {}).get("title") or record.get("title")
    if _words(found) != _words(title):
        return None, "Zenodo's record has another title than the metadata"
    return record, None


# ── Content (§8) ─────────────────────────────────────────────────────────

# C-01: what in a description runs or loads something, rather than formats
# it, the class of the cases a curator reads. dataset's sanitiser keeps none
# of it (descriptions.clean_html), so it only tells the cases apart.
ACTIVE_ELEMENTS = frozenset(
    {
        "applet",
        "base",
        "embed",
        "form",
        "frame",
        "frameset",
        "iframe",
        "link",
        "math",
        "meta",
        "object",
        "script",
        "style",
        "svg",
    }
)
ACTIVE_SCHEMES = ("javascript", "vbscript", "data")
URL_ATTRIBUTES = frozenset(
    {"action", "background", "formaction", "href", "poster", "src", "xlink:href"}
)


@dataclass(frozen=True)
class Markup:
    """What a description's HTML holds: the elements it uses, and what in
    it is active (an element, ``on<event>=`` or ``<attribute>=<scheme>:``)."""

    tags: frozenset
    active: tuple


class _MarkupReader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags, self.active = set(), set()

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag)
        if tag in ACTIVE_ELEMENTS:
            self.active.add(f"<{tag}>")
        for name, value in attrs:
            if name.startswith("on"):
                self.active.add(f"{name}=")
            elif name in URL_ATTRIBUTES:
                # A browser reads the scheme past blanks and control
                # characters, as "java\tscript:" (the parser already turned
                # the character references into characters).
                bare = "".join(c for c in value or "" if c.isprintable()).replace(
                    " ", ""
                )
                scheme = bare.split(":", 1)[0].lower() if ":" in bare else ""
                if scheme in ACTIVE_SCHEMES:
                    self.active.add(f"{name}={scheme}:")

    handle_startendtag = handle_starttag


def markup(html) -> Markup:
    """C-01 (P-22): the elements a description of v2.12 uses, for the
    frequency the plan asks of each, and what in it is active."""
    reader = _MarkupReader()
    reader.feed(str(html or ""))
    reader.close()
    return Markup(frozenset(reader.tags), tuple(sorted(reader.active)))


def publication_doi(value):
    """C-16: a publication DOI as dataset keeps one
    (creation.publication_doi_of): a DOI bare, whether v2.12 had it as
    https://doi.org/<doi> or doi:<doi>, an http(s) address as it is,
    trimmed, and "" for nothing. What is
    neither stays as v2.12 had it: dataset's readers (fair_metadata's
    article_identifier) name nothing they cannot read, and its owner's next
    edit asks for a DOI or an address. NULL stays NULL."""
    if value is None:
        return None
    found = publication_doi_of(value)
    return value if found is None else found


def normal_tags(value):
    """C-23 (with the tags kept a string, as decided): v2.12's
    comma-separated tags split, each on one line without blanks around it,
    the empty ones and the repeated ones gone, the spelling kept (a repeat
    is the same text exactly, as utf8mb4_bin compares it, DM-15), joined by
    "," as dataset writes them (creation.clean_tags). NULL stays NULL."""
    if value is None:
        return None
    kept = []
    for tag in str(value).split(","):
        tag = " ".join(tag.split())
        if tag and tag not in kept:
            kept.append(tag)
    return ",".join(kept)


#: §7.3: what a metrics row of v2.12 says it was extracted by, until
#: factlabel extracts it again.
LEGACY_METRICS = "legacy"


def legacy_extractor_version(version, limit: int) -> str:
    """§7.3: the extractor_version of a metrics row copied from v2.12,
    "legacy:<v2.12's>" within ``limit`` characters. The plan's status =
    'legacy' in factlabel's own terms: a row whose version is not its
    EXTRACTOR_VERSION is stale, so metrics-status counts it and
    metrics-backfill extracts it again from its FactLabel."""
    return f"{LEGACY_METRICS}:{version or ''}"[:limit]


def concept_chain(members):
    """C-05: the lineage the versions of one concept DOI make, as
    [(dataset id, origin id)], or None when it cannot be made.

    ``members`` are the datasets that carry the concept, as rows with id,
    created_at, dataset_version and dataset_origin_id. As the plan says
    (§8, C-05), they are ordered by created_at (then id), each stands on
    the one before, and dataset_version is never renumbered: so the
    versions must rise in that order, or the repair would number two
    versions alike or one before its origin, and None leaves the lineage
    to a decision (curation.toml). The first keeps the origin it has, unless
    that is one of the others, made after it: then it is the root."""
    ordered = sorted(members, key=lambda d: (d["created_at"], d["id"]))
    versions = [d["dataset_version"] or 1 for d in ordered]
    if any(later <= earlier for earlier, later in zip(versions, versions[1:])):
        return None
    first = ordered[0]
    origin = first["dataset_origin_id"]
    if origin in {d["id"] for d in ordered}:
        origin = None
    chain = [(first["id"], origin)]
    chain += [(d["id"], before["id"]) for before, d in zip(ordered, ordered[1:])]
    return chain


def zenodo_concept(snapshot, doi) -> str | None:
    """The concept DOI Zenodo gives the record of ``doi`` (§4.3, CT-4), when
    its record in zenodo_snapshot validates (zenodo_record)."""
    record = zenodo_record(snapshot, doi)
    concept = (record or {}).get("conceptdoi") or ""
    return concept.strip() or None


def zenodo_dates(snapshot, doi):
    """(created, published) of a dataset's record in zenodo_snapshot, as
    naive UTC, or None when there is no record or it does not validate
    (zenodo_record)."""
    record = zenodo_record(snapshot, doi)
    if record is None:
        return None
    created = published = None
    try:
        if record.get("created"):
            created = naive_utc(datetime.fromisoformat(record["created"]))
        day = (record.get("metadata") or {}).get("publication_date")
        if day:
            published = datetime.fromisoformat(day)
    except (TypeError, ValueError):
        return None
    if created is None and published is None:
        return None
    return created or published, published or created


def artifact_type(name: str) -> str:
    """hubfile0002's reading of a row that predates the column."""
    return "uvl" if (name or "").lower().endswith(".uvl") else "file"
