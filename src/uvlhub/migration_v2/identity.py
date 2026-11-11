"""E4, identity: user, user_profile, external_identity and api_token (§5).

Accounts are carried over unconfirmed (legacy_unconfirmed, DM-2): auth
signs them in, and asks them to confirm their address before what hands
the account over. Two things found in the source confirm one at once
(§5.1): a reset link mailed to exactly that address and followed
(legacy_reset), or a GitHub identity with exactly that address
(legacy_github). Never for a takeover candidate (P-26, C-28): an account
whose reset link went to another spelling of its address and was followed
loads unconfirmed and with must_reset_password (auth 1.26.0). Its password
is copied as it is, and opens nothing: signing in with it only mails the
owner a reset link, so whoever set it by that link is shut out.

What is not loaded, and why:

- the accounts of the development seed (P-25): dropped, for review;
- accounts whose addresses would clash in 3.0 (C-13): held, as conflicts,
  for a decision with security; with them, whatever is theirs. user.email
  is utf8mb4_bin since auth 1.26.0, so its unique key refuses only the very
  same text, and the clashes are the ones auth's canonical form finds
  (email_canonical's unique key): addresses v2.12's collation told apart
  that NFKC and casefold, or a stripped space, make one.

An identity's provider is written exactly, orcid or github: external_identity
compares it under utf8mb4_bin since identities 0.5.0, so "GitHub " would be
another provider there, where v2.12's collation took it for github. Any
other provider is a conflict.

Every account gets session_version 2. v2.12's remember-me cookie names the
bare id, which auth honours only at version 1 (auth's user_for_session),
so no cookie of v2.12 opens a session of 3.0, whatever DM-1 decides about
SECRET_KEY.
"""

from __future__ import annotations

from collections import defaultdict

import sqlalchemy as sa
from splent_io.splent_feature_apikeys.services import imported_token_fields
from splent_io.splent_feature_auth.models import ORIGIN_LEGACY, canonical_email

from uvlhub.migration_v2 import rules
from uvlhub.migration_v2.db import (
    all_rows,
    foreign_keys_off,
    insert_batches,
    qualified,
    reflect,
)
from uvlhub.migration_v2.ledger import HELD, ORPHAN, SEED, stop_on_conflicts

# The scopes of a v2.12 key that write (the plan's FIND_IN_SET('write_dataset')).
WRITING_SCOPES = ("write_dataset",)
SESSION_VERSION = 2
# The providers of v2.12's external_identity, as identities names them.
PROVIDERS = ("orcid", "github")
SOURCE_TABLES = (
    "user",
    "user_profile",
    "external_identity",
    "orcid",
    "github",
    "api_keys",
    "reset_token",
)
TARGET_TABLES = ("user", "user_profile", "external_identity", "api_token")


def collation_clashes(connection, schema: str, collation: str) -> list[list[int]]:
    """Groups of accounts whose addresses are one under ``collation``, the
    one user.email has in uvlhub3, whose UNIQUE would refuse all but one.

    Under utf8mb4_bin, what the contract says today, that is the very same
    text, which v2.12's own unique key never let in: it finds nothing, and
    stays as the guard of a contract that goes back to another collation."""
    rows = connection.execute(
        sa.text(
            f"SELECT GROUP_CONCAT(id ORDER BY id) FROM {qualified(schema, 'user')} "
            f"WHERE email IS NOT NULL GROUP BY email COLLATE {collation} "
            "HAVING COUNT(*) > 1"
        )
    ).scalars()
    return [[int(i) for i in ids.split(",")] for ids in rows]


def hold_clashing_accounts(ctx, connection, users) -> None:
    """C-13 (P-21): by auth's canonical form, which email_canonical's unique
    key compares, and by the collation of user.email in uvlhub3."""
    ledger = ctx.ledger
    groups = defaultdict(list)
    for user in users:
        canonical = canonical_email(user["email"])
        if canonical is not None:
            groups[("canonical", canonical)].append(user["id"])
    collation = ctx.contract.tables["user"].columns["email"].collation
    for ids in collation_clashes(connection, ctx.params.source_schema, collation):
        groups[("collation", ",".join(map(str, ids)))].extend(ids)
    by_id = {user["id"]: user for user in users}
    for (how, ref), ids in sorted(groups.items()):
        ids = [i for i in ids if not ledger.is_dropped("user", i)]
        if len(ids) < 2:
            continue
        ledger.conflict(
            f"email_clash_{how}",
            "user",
            ref,
            [by_id[i] for i in ids],
            detail=f"accounts {', '.join(map(str, ids))} share one address in 3.0",
        )
        for user_id in ids:
            ledger.drop("user", user_id, HELD, f"email_clash_{how}")


# What a reset link of v2.12 is (P-26): not such a link, a link for no
# account, one mailed to the account's very address, or one mailed to
# another spelling of it, which opened the account all the same.
NOT_A_LINK, NO_ACCOUNT, OWN, ANOTHER_SPELLING = (
    "not_a_link",
    "no_account",
    "own",
    "another_spelling",
)


def classify_reset_token(connection, user_table: str, token: str):
    """(what it is, the address typed, when it was issued, the account it
    opened) of a reset link of v2.12, read without its key (P-26)."""
    typed, issued = rules.decode_reset_token(token)
    if typed is None:
        return NOT_A_LINK, None, None, None
    # As v2.12 found the account: lowered, under the source's collation.
    account = connection.execute(
        sa.text(
            f"SELECT id, email FROM {user_table} WHERE email = :typed ORDER BY id LIMIT 1"
        ),
        {"typed": typed.strip().lower()},
    ).first()
    if account is None:
        return NO_ACCOUNT, typed, issued, None
    if rules.reset_matches_account(typed, account.email):
        return OWN, typed, issued, account
    return ANOTHER_SPELLING, typed, issued, account


def read_reset_tokens(ctx, connection, tokens):
    """P-26: (proofs by account, accounts with a link followed, takeovers)."""
    proofs, followed, takeovers = defaultdict(list), set(), set()
    user = qualified(ctx.params.source_schema, "user")
    for token in tokens:
        kind, typed, issued, account = classify_reset_token(
            connection, user, token["token"]
        )
        if kind == NOT_A_LINK:
            ctx.ledger.note("reset_token: not a reset link of v2.12")
            continue
        if kind == NO_ACCOUNT:
            ctx.ledger.note("reset_token: for no account")
            continue
        if token["used_at"] is not None:
            followed.add(account.id)
        if kind == OWN:
            if token["used_at"] is not None:
                proofs[account.id].append((rules.LEGACY_RESET, token["used_at"]))
            continue
        probable = "probable" if token["used_at"] is not None else "attempt"
        ctx.ledger.takeovers.append(
            {
                "reset_token_id": token["id"],
                "user_id": account.id,
                "typed": typed,
                "account_email": account.email,
                "issued_at": issued,
                "used_at": token["used_at"],
                "kind": probable,
            }
        )
        if probable == "probable":
            takeovers.add(account.id)
    return proofs, followed, takeovers


def build_users(ctx, users, proofs, followed, takeovers, identity_dates) -> list[dict]:
    params, ledger = ctx.params, ctx.ledger
    admins = {canonical_email(email) for email in params.admin_emails}
    rows = []
    for user in users:
        if ledger.is_dropped("user", user["id"]):
            continue
        taken_over = user["id"] in takeovers
        via, at = (None, None) if taken_over else rules.legacy_proof(proofs[user["id"]])
        canonical = canonical_email(user["email"])
        rows.append(
            {
                "id": user["id"],
                "email": user["email"],
                "email_canonical": canonical,
                "pending_email": None,
                "password": user["password"],
                "created_at": user["created_at"],
                "role": "admin"
                if canonical is not None and canonical in admins
                else "user",
                "email_verified_at": at,
                "email_verified_via": via,
                "disabled_at": None if user["active"] else params.t0,
                "last_login_at": None,
                "password_changed_at": None,
                "session_version": SESSION_VERSION,
                "account_origin": ORIGIN_LEGACY,
                "has_usable_password": rules.has_usable_password(
                    user["created_at"],
                    identity_dates[user["id"]],
                    user["id"] in followed,
                ),
                "is_service_account": False,
                # C-28: whoever followed the link may know the password,
                # so it opens nothing until the owner resets it.
                "must_reset_password": taken_over,
            }
        )
    by_canonical = {row["email_canonical"]: row["id"] for row in rows}
    ctx.admins = [
        by_canonical[canonical_email(email)]
        for email in params.admin_emails
        if canonical_email(email) in by_canonical
    ]
    ctx.facts["admins_missing"] = sorted(
        email
        for email in params.admin_emails
        if canonical_email(email) not in by_canonical
    )
    return rows


def build_profiles(ctx, profiles, loaded_users) -> list[dict]:
    rows = []
    for profile in profiles:
        if profile["user_id"] not in loaded_users:
            ctx.ledger.drop(
                "user_profile",
                profile["id"],
                ctx.ledger.owner_reason(profile["user_id"]),
            )
            continue
        rows.append(
            {
                "id": profile["id"],
                "user_id": profile["user_id"],
                "name": profile["name"].strip(),
                "surname": profile["surname"].strip(),
                "affiliation": (
                    profile["affiliation"].strip()
                    if profile["affiliation"] is not None
                    else None
                ),
            }
        )
    return rows


def _normalized_provider_id(provider, value):
    if provider == "orcid":
        return rules.normalize_orcid(value)
    return value


def build_identities(
    ctx, identities, orcids, githubs, profiles, users_by_id, loaded_users
):
    """external_identity of v2.12 with the orcid and github tables folded
    in (§5.6). Rows of external_identity keep their ids; a folded row that
    adds an identity takes a new one above the source's counter."""
    ledger = ctx.ledger
    user_of_profile = {profile["id"]: profile["user_id"] for profile in profiles}

    base = []
    for identity in identities:
        if identity["user_id"] not in loaded_users:
            ledger.drop(
                "external_identity",
                identity["id"],
                ledger.owner_reason(identity["user_id"]),
            )
            continue
        provider = (identity["provider"] or "").strip().lower()
        if provider not in PROVIDERS:
            ledger.conflict(
                "identity_unknown_provider",
                "external_identity",
                identity["id"],
                [identity],
                detail=f"{identity['provider']!r} is no provider of uvlhub",
            )
            ledger.drop(
                "external_identity", identity["id"], HELD, "identity_unknown_provider"
            )
            continue
        if provider != identity["provider"]:
            ledger.note("external_identity: provider written exactly")
        provider_id = _normalized_provider_id(provider, identity["provider_id"])
        if provider_id is None:
            ledger.conflict(
                "identity_invalid_id",
                "external_identity",
                identity["id"],
                [identity],
                detail=f"{identity['provider_id']!r} is not a valid ORCID iD",
            )
            ledger.drop(
                "external_identity", identity["id"], HELD, "identity_invalid_id"
            )
            continue
        base.append(dict(identity, provider=provider, provider_id=provider_id))

    # P-11: an account that links two of one provider breaks
    # UNIQUE(user_id, provider); which link stays is a decision.
    pairs = defaultdict(list)
    for identity in base:
        pairs[(identity["user_id"], identity["provider"])].append(identity)
    source_of = {identity["id"]: identity for identity in identities}
    held = set()
    for (user_id, provider), group in sorted(pairs.items()):
        if len(group) > 1:
            ledger.conflict(
                "identity_second_link",
                "external_identity",
                f"{user_id}:{provider}",
                [source_of[identity["id"]] for identity in group],
                detail=f"user {user_id} links {len(group)} {provider} accounts",
            )
            for identity in group:
                held.add(identity["id"])
                ledger.drop(
                    "external_identity", identity["id"], HELD, "identity_second_link"
                )
    base = [identity for identity in base if identity["id"] not in held]

    rows = {
        identity["id"]: {
            "id": identity["id"],
            "user_id": identity["user_id"],
            "provider": identity["provider"],
            "provider_id": identity["provider_id"],
            "provider_username": identity["provider_username"],
            "created_at": identity["created_at"],
            "provider_email_verified": rules.provider_email_verified(
                identity["provider"],
                identity["email"],
                users_by_id[identity["user_id"]]["email"],
            ),
        }
        for identity in base
    }
    counter = ctx.source_counters.get("external_identity")
    next_id = max(counter or 1, max((i["id"] for i in identities), default=0) + 1)

    for provider, table in (("orcid", orcids), ("github", githubs)):
        rows_by_id = {row["id"]: row for row in table}
        candidates = []
        for row in table:
            user_id = user_of_profile.get(row["profile_id"])
            if user_id is not None and user_id not in loaded_users:
                ledger.drop(provider, row["id"], ledger.owner_reason(user_id))
                continue
            if provider == "orcid":
                # The iD is the username of an ORCID identity (orcid0002).
                provider_id = username = rules.normalize_orcid(row["orcid_id"])
                if provider_id is None:
                    ledger.conflict(
                        "identity_invalid_id",
                        provider,
                        row["id"],
                        [row],
                        detail=f"{row['orcid_id']!r} is not a valid ORCID iD",
                    )
                    ledger.drop(provider, row["id"], HELD, "identity_invalid_id")
                    continue
            else:
                provider_id = str(row["github_id"])
                username = (row["github_login"] or "").strip() or None
            candidates.append(
                (row["id"], provider_id, username, row["registration_date"], user_id)
            )
        existing = [
            (
                row["id"],
                row["user_id"],
                row["provider_id"],
                row["provider_username"],
                row["created_at"],
            )
            for row in rows.values()
            if row["provider"] == provider
        ]
        inserts, updates, conflicts = rules.fold_identities(
            provider, candidates, existing
        )
        for identity_id, values in updates:
            rows[identity_id].update(values)
        for insert in inserts:
            rows[next_id] = dict(insert, id=next_id, provider_email_verified=None)
            next_id += 1
        refused = set()
        for row_id, kind, detail in conflicts:
            refused.add(row_id)
            if kind == rules.FOLD_ORPHAN:
                ledger.drop(provider, row_id, ORPHAN, detail)
                continue
            ledger.conflict(
                f"identity_{kind}",
                provider,
                row_id,
                [rows_by_id[row_id]],
                detail=detail,
            )
            ledger.drop(provider, row_id, HELD, f"identity_{kind}")
        identity_of = {
            row["provider_id"]: row["id"]
            for row in rows.values()
            if row["provider"] == provider
        }
        for row_id, provider_id, _username, _date, _user_id in candidates:
            if row_id not in refused:
                ledger.map(
                    provider, row_id, "external_identity", identity_of[provider_id]
                )
    return list(rows.values())


def build_tokens(ctx, keys, loaded_users) -> list[dict]:
    """§5.5, D12: each key as apikeys' imported_token_fields gives its row,
    the very fields ApiTokenService.import_token stores, without a session."""
    params, ledger = ctx.params, ctx.ledger
    rows = []
    for key in keys:
        if key["user_id"] not in loaded_users:
            ledger.drop("api_keys", key["id"], ledger.owner_reason(key["user_id"]))
            continue
        scopes, gone = rules.translate_scopes(key["scopes"], ctx.contract.scopes)
        for name in gone:
            ledger.note(f"api_keys: scope {name} has no equivalent")
        writes = any(scope in WRITING_SCOPES for scope in scopes)
        stamp = key["created_at"]
        fields = imported_token_fields(
            key["user_id"],
            key["key"],
            name="uvlhub 2 key" + (f" ({stamp:%Y-%m-%d})" if stamp else ""),
            scopes=scopes,
            now=params.t0,
            created_at=key["created_at"],
            last_used_at=key["last_used_at"],
            ttl_days=params.ttl_write_days if writes else params.ttl_read_days,
            token_id=key["id"],
            never_used_grace_days=params.never_used_grace_days,
            unused_days=params.unused_days,
        )
        # Aware UTC, as the model keeps them; the DATETIME columns hold the
        # same moment without its zone.
        row = {name: rules.naive_utc(value) for name, value in fields.items()}
        row["expiry_notice_days"] = None
        rows.append(row)
    return rows


def identity(ctx) -> None:
    params, ledger = ctx.params, ctx.ledger
    with ctx.engine.connect() as connection:
        src = reflect(connection, params.source_schema, only=SOURCE_TABLES)
        tgt = reflect(connection, params.target_schema, only=TARGET_TABLES)
        users = all_rows(connection, src["user"])
        profiles = all_rows(connection, src["user_profile"])
        identities = all_rows(connection, src["external_identity"])
        orcids = all_rows(connection, src["orcid"])
        githubs = all_rows(connection, src["github"])
        keys = all_rows(connection, src["api_keys"])
        tokens = all_rows(connection, src["reset_token"])

        for user in users:
            if rules.is_seed_email(user["email"]):
                ledger.drop("user", user["id"], SEED, user["email"])
        hold_clashing_accounts(ctx, connection, users)
        proofs, followed, takeovers = read_reset_tokens(ctx, connection, tokens)
        connection.rollback()

    users_by_id = {user["id"]: user for user in users}
    loadable = {
        user["id"] for user in users if not ledger.is_dropped("user", user["id"])
    }
    identity_rows = build_identities(
        ctx, identities, orcids, githubs, profiles, users_by_id, loadable
    )
    # legacy_github: an identity that loads, whose address GitHub gave is
    # the account's, byte for byte. One held by a conflict proves nothing
    # until the conflict is decided.
    linked = {row["id"] for row in identity_rows}
    for identity_row in identities:
        user = users_by_id.get(identity_row["user_id"])
        if (
            identity_row["id"] in linked
            and identity_row["provider"] == "github"
            and user is not None
            and user["email"] is not None
            and identity_row["email"] == user["email"]
        ):
            proofs[user["id"]].append((rules.LEGACY_GITHUB, identity_row["created_at"]))

    user_of_profile = {profile["id"]: profile["user_id"] for profile in profiles}
    identity_dates = defaultdict(list)
    for identity_row in identities:
        identity_dates[identity_row["user_id"]].append(identity_row["created_at"])
    for row in orcids + githubs:
        user_id = user_of_profile.get(row["profile_id"])
        if user_id is not None:
            identity_dates[user_id].append(row["registration_date"])

    user_rows = build_users(ctx, users, proofs, followed, takeovers, identity_dates)
    loaded = {row["id"] for row in user_rows}
    profile_rows = build_profiles(ctx, profiles, loaded)
    token_rows = build_tokens(ctx, keys, loaded)

    with ctx.engine.connect() as connection, foreign_keys_off(connection):
        insert_batches(connection, tgt["user"], user_rows)
        insert_batches(connection, tgt["user_profile"], profile_rows)
        insert_batches(connection, tgt["external_identity"], identity_rows)
        insert_batches(connection, tgt["api_token"], token_rows)

    ctx.loaded["user"] = loaded
    ctx.loaded["user_profile"] = {row["id"] for row in profile_rows}
    ctx.loaded["external_identity"] = {row["id"] for row in identity_rows}
    ctx.loaded["api_keys"] = {row["id"] for row in token_rows}
    ctx.takeover_users = takeovers
    ledger.count("user", len(users), len(user_rows))
    ledger.count("user_profile", len(profiles), len(profile_rows))
    ledger.count(
        "external_identity",
        len(identities),
        len(identity_rows),
        {"orcid": len(orcids), "github": len(githubs)},
    )
    ledger.count("orcid", len(orcids), sum(1 for k in ledger.id_map if k[0] == "orcid"))
    ledger.count(
        "github", len(githubs), sum(1 for k in ledger.id_map if k[0] == "github")
    )
    ledger.count("api_keys", len(keys), len(token_rows))
    ledger.count(
        "reset_token",
        len(tokens),
        0,
        {
            "legacy_reset": sum(
                1
                for row in user_rows
                if row["email_verified_via"] == rules.LEGACY_RESET
            ),
            "legacy_github": sum(
                1
                for row in user_rows
                if row["email_verified_via"] == rules.LEGACY_GITHUB
            ),
            "takeover_probable": len(takeovers),
        },
    )
    stop_on_conflicts(ctx, "E4")
