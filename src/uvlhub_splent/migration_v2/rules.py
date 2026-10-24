"""The rules of the migration that need no database: each one a function the
tests call directly.

The domain rules belong to the pinned features and are imported from them
(principle 4): auth's canonical_email, dataset's state_from_metadata,
hubfile's checksum_algorithm, apikeys' imported_token_fields (the row
ApiTokenService.import_token stores, without a session). One lives in an
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
from datetime import datetime, timezone

from itsdangerous.encoding import base64_decode
from itsdangerous.exc import BadData

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


def decode_reset_token(token: str):
    """(address, issued at) a reset link of v2.12 carries, read without its
    key (P-26), or (None, None) for one that is not such a link.

    The link is itsdangerous' URLSafeTimedSerializer: the payload, the time
    and the signature, joined by dots. The payload is base64url JSON,
    zlib-compressed when it starts with a dot; the time is a big-endian
    integer of seconds, in base64url too.
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
    except (BadData, ValueError, TypeError, zlib.error, OverflowError, OSError):
        return None, None
    if not isinstance(payload, str):
        return None, None
    return payload, issued


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


def zenodo_dates(snapshot, doi):
    """(created, published) of a dataset's record in zenodo_snapshot, as
    naive UTC, or None when there is no record or it does not validate: its
    sha256 is not the snapshot's, or its DOI is not ``doi`` (§4.3, compared
    without case or surrounding spaces). ``snapshot`` is the row of
    uvlhub_migration_inputs.zenodo_snapshot, or None."""
    if snapshot is None:
        return None
    text = snapshot["record"] or ""
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != snapshot["sha256"]:
        return None
    try:
        record = json.loads(text)
    except ValueError:
        return None
    if not isinstance(record, dict) or (record.get("doi") or "").strip().lower() != (
        (doi or "").strip().lower()
    ):
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
