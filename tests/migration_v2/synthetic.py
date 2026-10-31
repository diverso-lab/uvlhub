"""A dirty uvlhub.io 2.12 (R0, §9.1): the monolith's schema and a row for
each anomaly of §2 and §8 the migrator has a rule for.

Who is who, so a test can say what it expects:

    accounts  1 alice   admin, ORCID (orcid table and external_identity),
                        a reset link followed (legacy_reset), many datasets
              2 bob     GitHub, opened through it (no usable password), the
                        same address there (legacy_github)
              3 jose    a reset link asked as "josé@" and followed: a probable
                        takeover (P-26, C-28)
              4 mar     a link asked as "már@" never followed (an attempt),
                        and one of its own followed
              5, 6      the development seed (P-25)
              7         switched off (active = 0)
              8         GitHub without an address, opened through it
              9         no profile
             10, 11     addresses one under utf8mb4_unicode_ci, apart under the
                        utf8mb4_bin user.email has: both load
             12 carol   an ORCID iD here, another in external_identity
             13 dave    two GitHub identities (P-11)
             14 erin    a GitHub row only, and an ORCID row with carol's iD
             15 frank   an ORCID row whose iD is not valid
             16, 17     one address but for a leading space, which v2.12's
                        unique key let in and the canonical form does not
                        (C-13), the only such pair its collation allows; 17
                        owns a dataset and a GitHub identity

    identities also with a provider written "GitHub " (it is github) and
    one that is no provider of uvlhub (gitlab)

    datasets  1  published, two files, one in a sub folder with " " and "#"
              2  version 2 of 1, its file's checksum an md5 (C-24)
              3  sync pending, its file in mismatch with its row
              4  a deposition without a DOI (failed)
              5  a draft whose file is missing
              6  a ghost draft (DM-3)
              7  anonymous, with authors (DS-3)
              8  a sandbox DOI (C-30)
              9, 10  one DOI (C-10); 9 with NULL publication type and anonymity
             11  owned by a held account (17)
             12  the seed's
             13  a draft with two rows on one path (C-11), a checksum of no
                 algorithm (C-25) and a feature model of dataset 5's file (C-07)
             14  version 2 of 1 as well: a branch (C-05)

and metadata without a dataset: two with a DOI (290, which the Zenodo
snapshot dates, and 292, anonymous, which nothing dates) and one without
(291); an author of no metadata, votes to move, to merge and to drop,
transfers, the usage records E6 aggregates (and the ones it may not), DOI
mappings with a chain, a cycle and a dead end, a trigger and a view (P-28),
and counters ahead of the rows, as when the last row was deleted (§4.1).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

import sqlalchemy as sa
from itsdangerous import TimestampSigner, URLSafeTimedSerializer
from werkzeug.security import generate_password_hash

from uvlhub_splent.migration_v2 import v2_12_schema
from uvlhub_splent.migration_v2.rules import orcid_check_digit

T0 = datetime(2026, 11, 20)
SECRET_KEY = "the SECRET_KEY of a synthetic uvlhub 2.12"
RESET_SALT = "email-confirm"


def ago(days: float = 0, **delta) -> datetime:
    return T0 - timedelta(days=days, **delta)


def orcid(first15: str) -> str:
    digits = first15 + orcid_check_digit(first15)
    return "-".join(digits[i : i + 4] for i in range(0, 16, 4))


ALICE_ORCID = orcid("000000021694233")  # 0000-0002-1694-233X
CAROL_ORCID = orcid("000000015109370")
CAROL_OTHER_ORCID = orcid("000000034567890")
JOSE_ORCID = orcid("000000027777777")
ORPHAN_ORCID = orcid("000000029999999")
INVALID_ORCID = "0000-0000-0000-0000"


class _FixedTime(TimestampSigner):
    """Links signed at one moment, so the synthetic source is the same on
    every run."""

    def get_timestamp(self) -> int:
        return int(datetime(2026, 1, 15).timestamp())


def reset_link(address: str) -> str:
    """A reset link of v2.12 (mono/app/features/reset/services.py)."""
    return URLSafeTimedSerializer(SECRET_KEY, signer=_FixedTime).dumps(
        address, salt=RESET_SALT
    )


def api_key(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def md5(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


def uvl(name: str) -> bytes:
    return f"features\n    {name}\n        optional\n            Leaf\n".encode()


_PASSWORDS = {}


def password(user_id: int, clear: str | None = None) -> str:
    if user_id not in _PASSWORDS:
        _PASSWORDS[user_id] = generate_password_hash(
            clear or f"secret-{user_id}", method="pbkdf2:sha256:1000"
        )
    return _PASSWORDS[user_id]


def users():
    rows = [
        (1, "alice@uvlhub.test", ago(500)),
        (2, "bob@uvlhub.test", datetime(2025, 1, 10, 10, 0, 0)),
        (3, "jose@uvlhub.test", ago(400)),
        (4, "mar@uvlhub.test", ago(390)),
        (5, "user1@example.com", ago(600)),
        (6, "user2@example.com", ago(600)),
        (7, "inactive@uvlhub.test", ago(300)),
        (8, None, datetime(2025, 4, 1, 12, 0, 0)),
        (9, "noprofile@uvlhub.test", ago(200)),
        (10, "clash\U0001f600@uvlhub.test", ago(150)),
        (11, "clash\U0001f601@uvlhub.test", ago(149)),
        (12, "carol@uvlhub.test", ago(450)),
        (13, "dave@uvlhub.test", ago(120)),
        (14, "erin@uvlhub.test", ago(110)),
        (15, "frank@uvlhub.test", ago(100)),
        (16, "shared@uvlhub.test", ago(90)),
        (17, " shared@uvlhub.test", ago(80)),
    ]
    return [
        {
            "id": user_id,
            "email": email,
            "password": password(user_id, "1234" if user_id in (5, 6) else None),
            "created_at": created,
            "active": user_id != 7,
        }
        for user_id, email, created in rows
    ]


def profiles():
    names = {
        1: (" Alice ", " Liddell ", " Universidad de Sevilla "),
        2: ("Bob", "Builder", None),
        3: ("José", "García", "US"),
        4: ("Mar", "Pérez", None),
        5: ("John", "Doe", "Some University"),
        6: ("Jane", "Doe", "Some University"),
        7: ("Ina", "Ctive", None),
        8: ("Git", "Hub", None),
        10: ("Clash", "One", None),
        11: ("Clash", "Two", None),
        12: ("Carol", "Danvers", None),
        13: ("Dave", "Lister", None),
        14: ("Erin", "Brockovich", None),
        15: ("Frank", "Castle", None),
        16: ("Sha", "Red", None),
        17: ("Sha", "Red Too", None),
    }
    # The profile id is the user id plus 100, so a test never mixes them.
    return [
        {"id": 100 + uid, "user_id": uid, "name": n, "surname": s, "affiliation": a}
        for uid, (n, s, a) in names.items()
    ]


def external_identities():
    return [
        {
            "id": 1,
            "user_id": 1,
            "provider": "orcid",
            "provider_id": ALICE_ORCID,
            "email": "alice@uvlhub.test",
            "created_at": datetime(2025, 3, 1),
            "provider_username": None,
        },
        {
            "id": 2,
            "user_id": 2,
            "provider": "github",
            "provider_id": "1001",
            "email": "bob@uvlhub.test",
            "created_at": datetime(2025, 1, 10, 10, 0, 2),
            "provider_username": "bobgh",
        },
        {
            "id": 3,
            "user_id": 8,
            "provider": "github",
            "provider_id": "1002",
            "email": None,
            "created_at": datetime(2025, 4, 1, 12, 0, 1),
            "provider_username": "nomail",
        },
        {
            "id": 4,
            "user_id": 12,
            "provider": "orcid",
            "provider_id": CAROL_ORCID,
            "email": "carol@uvlhub.test",
            "created_at": ago(440),
            "provider_username": CAROL_ORCID,
        },
        {
            "id": 5,
            "user_id": 13,
            "provider": "github",
            "provider_id": "1003",
            "email": "dave@uvlhub.test",
            "created_at": ago(119),
            "provider_username": "dave1",
        },
        {
            "id": 6,
            "user_id": 13,
            "provider": "github",
            "provider_id": "1004",
            "email": "dave@uvlhub.test",
            "created_at": ago(118),
            "provider_username": "dave2",
        },
        {
            "id": 7,
            "user_id": 17,
            "provider": "github",
            "provider_id": "1005",
            "email": None,
            "created_at": ago(79),
            "provider_username": "shared",
        },
        {
            "id": 8,
            "user_id": 9,
            "provider": "GitHub ",
            "provider_id": "3001",
            "email": None,
            "created_at": ago(150),
            "provider_username": "noprofile",
        },
        {
            "id": 9,
            "user_id": 4,
            "provider": "gitlab",
            "provider_id": "mar-gl",
            "email": "mar@uvlhub.test",
            "created_at": ago(60),
            "provider_username": "mar",
        },
    ]


def orcids():
    return [
        {
            "id": 1,
            "orcid_id": ALICE_ORCID,
            "registration_date": datetime(2025, 2, 1),
            "profile_id": 101,
        },
        {
            "id": 2,
            "orcid_id": CAROL_OTHER_ORCID,
            "registration_date": ago(430),
            "profile_id": 112,
        },
        {
            "id": 3,
            "orcid_id": CAROL_ORCID,
            "registration_date": ago(100),
            "profile_id": 114,
        },
        {
            "id": 4,
            "orcid_id": ORPHAN_ORCID,
            "registration_date": ago(90),
            "profile_id": None,
        },
        {
            "id": 5,
            "orcid_id": INVALID_ORCID,
            "registration_date": ago(95),
            "profile_id": 115,
        },
        {
            "id": 6,
            "orcid_id": JOSE_ORCID.lower(),
            "registration_date": ago(380),
            "profile_id": 103,
        },
    ]


def githubs():
    return [
        {
            "id": 1,
            "github_id": 1001,
            "github_login": "bobgh",
            "registration_date": datetime(2025, 1, 10, 10, 0, 1),
            "profile_id": 102,
        },
        {
            "id": 2,
            "github_id": 2001,
            "github_login": " erin-gh ",
            "registration_date": ago(105),
            "profile_id": 114,
        },
    ]


def api_keys():
    rows = [
        (1, 1, "read_dataset", ago(100), ago(2)),
        (2, 1, "read_dataset,write_dataset", ago(90), ago(1)),
        (3, 2, "", ago(80), ago(3)),
        (4, 2, "read_dataset", ago(60), None),
        (5, 3, "read_dataset", ago(5), None),
        (6, 4, "write_dataset", ago(500), ago(400)),
        (7, 4, "read_dataset", None, ago(10)),
        (8, 5, "read_dataset", ago(300), ago(1)),
        (9, 1, "read_dataset,admin_magic", ago(20), ago(4)),
    ]
    return [
        {
            "id": i,
            "key": api_key(f"key-{i}"),
            "user_id": u,
            "scopes": s,
            "created_at": c,
            "last_used_at": last,
        }
        for i, u, s, c, last in rows
    ]


def reset_tokens():
    return [
        {"id": 1, "token": reset_link("alice@uvlhub.test"), "used_at": ago(200)},
        {"id": 2, "token": reset_link("josé@uvlhub.test"), "used_at": ago(150)},
        {"id": 3, "token": reset_link("már@uvlhub.test"), "used_at": None},
        {"id": 4, "token": reset_link("mar@uvlhub.test"), "used_at": ago(50)},
        {"id": 5, "token": "not-a-link-of-v2.12", "used_at": None},
        {"id": 6, "token": reset_link("nobody@uvlhub.test"), "used_at": ago(40)},
        # Long enough for itsdangerous to compress it.
        {"id": 7, "token": reset_link("a" * 80 + "@uvlhub.test"), "used_at": None},
    ]


# Datasets: id -> (owner, created, doi, deposition, synced, anonymous,
# publication type, origin, version, ds_metrics).
DATASETS = {
    1: (1, ago(300), "10.5281/zenodo.1001", 1001, 1, 0, "JOURNAL_ARTICLE", None, 1, 1),
    2: (1, ago(200), "10.5281/zenodo.1003", 1003, 1, 0, "JOURNAL_ARTICLE", 1, 2, 2),
    3: (2, ago(150), "10.5281/zenodo.1005", 1005, 0, 0, "REPORT", None, 1, None),
    4: (2, ago(140), None, 1007, 1, 0, "OTHER", None, 1, None),
    5: (1, ago(5), None, None, 1, 0, None, None, 1, None),
    6: (1, ago(60), None, None, 1, 0, None, None, 1, None),
    7: (12, ago(130), "10.5281/zenodo.1009", 1009, 1, 1, "THESIS", None, 1, None),
    8: (12, ago(125), "10.5072/zenodo.55", 55, 1, 0, "OTHER", None, 1, None),
    9: (12, ago(120), "10.5281/zenodo.1011", 1011, 1, None, None, None, 1, None),
    10: (14, ago(119), "10.5281/zenodo.1011", 1012, 1, 0, "OTHER", None, 1, None),
    11: (17, ago(100), "10.5281/zenodo.1013", 1013, 1, 0, "OTHER", None, 1, None),
    12: (5, ago(590), "10.1234/dataset1", 1, 1, 0, "DATA_MANAGEMENT_PLAN", None, 1, 3),
    13: (1, ago(3), None, None, 1, 0, None, None, 1, None),
    14: (1, ago(190), "10.5281/zenodo.1015", 1015, 1, 0, "JOURNAL_ARTICLE", 1, 2, None),
}
CONCEPT_DOI = "10.5281/zenodo.1000"
ORPHAN_DOI = "10.5281/zenodo.2001"
UNDATED_DOI = "10.5281/zenodo.2003"

# Files: id -> (dataset, feature model, directory, name, kind), where kind
# says what the mirror holds: "sha256" or "md5" (it matches), "mismatch"
# (another content), "missing" (none), "seed" or "unknown" (a checksum of no
# algorithm). The feature model id is the hubfile id plus 50.
HUBFILES = {
    1: (1, 51, "", "model one.uvl", "sha256"),
    2: (1, 52, "sub dir/a#b", "b#2.uvl", "sha256"),
    3: (2, 53, "", "model one.uvl", "md5"),
    4: (3, 54, "", "drift.uvl", "mismatch"),
    5: (4, 55, "", "failed.uvl", "sha256"),
    6: (5, 56, "", "gone.uvl", "missing"),
    7: (7, 57, "", "anon.uvl", "sha256"),
    8: (8, 58, "", "sandbox.uvl", "sha256"),
    9: (9, 59, "", "twin.uvl", "sha256"),
    10: (10, 60, "", "twin.uvl", "sha256"),
    11: (11, 61, "", "held.uvl", "sha256"),
    12: (12, 62, "", "file1.uvl", "seed"),
    13: (13, 63, "", "dup.uvl", "sha256"),
    14: (13, 64, "", "dup.uvl", "sha256"),
    15: (13, 65, "", "odd.uvl", "unknown"),
    16: (5, 66, "", "moved.uvl", "sha256"),
    17: (14, 67, "", "branch.uvl", "sha256"),
}
# Feature model 66 says dataset 13; its file is dataset 5's (C-07).
FEATURE_MODEL_DATASET = {66: 13}


def content_of(hubfile_id: int) -> bytes:
    _dataset, _fm, _folder, name, _kind = HUBFILES[hubfile_id]
    # Two rows on one path share their file, as in v2.12's uploads/.
    if hubfile_id == 14:
        hubfile_id = 13
    return uvl(
        f"Root{hubfile_id}_{name.split('.')[0].replace(' ', '_').replace('#', '_')}"
    )


def checksum_of(hubfile_id: int) -> str:
    kind = HUBFILES[hubfile_id][4]
    content = content_of(hubfile_id)
    if kind == "md5":
        return md5(content)
    if kind == "seed":
        return f"checksum{hubfile_id}"
    if kind == "unknown":
        return "deadbeef"
    return sha256(content)


def content_rows():
    metas, datasets, fms, files = [], [], [], []
    for dataset_id, (
        owner,
        created,
        doi,
        deposition,
        synced,
        anonymous,
        kind,
        origin,
        version,
        metrics,
    ) in DATASETS.items():
        seed = dataset_id == 12
        metas.append(
            {
                "id": 200 + dataset_id,
                "deposition_id": deposition,
                "title": "Sample dataset 1" if seed else f"Dataset {dataset_id}",
                "description": f"<p>About dataset {dataset_id}</p><script>alert({dataset_id})</script>",
                "publication_type": kind,
                "publication_doi": f"https://doi.org/10.1000/paper{dataset_id}"
                if doi
                else None,
                "dataset_doi": doi,
                "dataset_concept_doi": CONCEPT_DOI
                if dataset_id in (1, 2, 14)
                else None,
                "tags": "tag1, tag2" if seed else "uvl, models",
                "ds_metrics_id": metrics,
                "dataset_anonymous": anonymous,
                "metadata_synced": synced,
                "api_publisher_user_id": 5 if dataset_id == 4 else None,
            }
        )
        datasets.append(
            {
                "id": dataset_id,
                "user_id": owner,
                "ds_meta_data_id": 200 + dataset_id,
                "created_at": created,
                "feature_model_count": 3 if seed else 1,
                "dataset_version": version,
                "dataset_origin_id": origin,
            }
        )
    metas += [
        {
            "id": 290,
            "deposition_id": 2001,
            "title": "Deleted, with a DOI",
            "description": "",
            "publication_type": "OTHER",
            "publication_doi": None,
            "dataset_doi": ORPHAN_DOI,
            "dataset_concept_doi": None,
            "tags": None,
            "ds_metrics_id": None,
            "dataset_anonymous": 0,
            "metadata_synced": 1,
            "api_publisher_user_id": None,
        },
        {
            "id": 292,
            "deposition_id": 2003,
            "title": "Deleted, anonymous",
            "description": "",
            "publication_type": "OTHER",
            "publication_doi": None,
            "dataset_doi": UNDATED_DOI,
            "dataset_concept_doi": None,
            "tags": None,
            "ds_metrics_id": None,
            "dataset_anonymous": 1,
            "metadata_synced": 1,
            "api_publisher_user_id": None,
        },
        {
            "id": 291,
            "deposition_id": None,
            "title": "Deleted draft",
            "description": "",
            "publication_type": None,
            "publication_doi": None,
            "dataset_doi": None,
            "dataset_concept_doi": None,
            "tags": None,
            "ds_metrics_id": None,
            "dataset_anonymous": 0,
            "metadata_synced": 1,
            "api_publisher_user_id": None,
        },
    ]
    for hubfile_id, (dataset_id, fm_id, folder, name, _kind) in HUBFILES.items():
        fms.append(
            {"id": fm_id, "dataset_id": FEATURE_MODEL_DATASET.get(fm_id, dataset_id)}
        )
        files.append(
            {
                "id": hubfile_id,
                "name": name,
                "checksum": checksum_of(hubfile_id),
                "size": len(content_of(hubfile_id)),
                "feature_model_id": fm_id,
                "dataset_id": dataset_id,
                "directory_path": folder,
            }
        )
    authors = [
        {
            "id": 1,
            "name": "Alice Liddell",
            "affiliation": "US",
            "orcid": ALICE_ORCID.lower(),
            "ds_meta_data_id": 201,
        },
        {
            "id": 2,
            # "Family, Given": dataset 0.9.0 keeps the names apart.
            "name": "Builder, Bob",
            "affiliation": None,
            "orcid": INVALID_ORCID,
            "ds_meta_data_id": 201,
        },
        {
            "id": 3,
            # Two commas: the names are not split on a guess.
            "name": "Liddell, Alice, PhD",
            "affiliation": "US",
            "orcid": ALICE_ORCID,
            "ds_meta_data_id": 202,
        },
        {
            "id": 4,
            "name": "Carol Danvers",
            "affiliation": "Kree",
            "orcid": CAROL_ORCID,
            "ds_meta_data_id": 207,
        },
        {
            "id": 5,
            "name": "Hidden Two",
            "affiliation": None,
            "orcid": None,
            "ds_meta_data_id": 207,
        },
        {
            "id": 6,
            "name": "Nobody's",
            "affiliation": None,
            "orcid": None,
            "ds_meta_data_id": None,
        },
        {
            "id": 7,
            "name": "Of a deleted dataset",
            "affiliation": None,
            "orcid": None,
            "ds_meta_data_id": 290,
        },
        {
            "id": 9,
            "name": "Hidden Author",
            "affiliation": None,
            "orcid": None,
            "ds_meta_data_id": 292,
        },
        {
            "id": 8,
            "name": "Author 1",
            "affiliation": "Affiliation 1",
            "orcid": "0000-0000-0000-0000",
            "ds_meta_data_id": 212,
        },
    ]
    metrics = [
        {"id": 1, "number_of_models": 2, "number_of_features": 0},
        {"id": 2, "number_of_models": 1, "number_of_features": 0},
        {"id": 3, "number_of_models": 5, "number_of_features": 50},
    ]
    return metas, datasets, fms, files, authors, metrics


def ratings():
    rows = [
        (1, 2, 1, True, ago(30), ago(30)),
        (2, 2, 2, True, ago(12), ago(10)),
        (3, 1, 1, True, ago(25), ago(25)),
        (4, 12, 14, False, ago(20), ago(20)),
        (5, 3, 7, True, ago(15), ago(15)),
        (6, 5, 1, True, ago(14), ago(14)),
    ]
    return [
        {
            "id": i,
            "user_id": u,
            "dataset_id": d,
            "is_like": like,
            "created_at": c,
            "updated_at": up,
        }
        for i, u, d, like, c, up in rows
    ]


def transfers():
    return [
        {
            "id": 1,
            "dataset_id": 1,
            "from_user_id": 1,
            "to_user_id": 2,
            "status": "PENDING",
            "message": "yours",
            "created_at": ago(9),
            "resolved_at": None,
        },
        {
            "id": 2,
            "dataset_id": 7,
            "from_user_id": 12,
            "to_user_id": 14,
            "status": "DECLINED",
            "message": None,
            "created_at": ago(40),
            "resolved_at": ago(39),
        },
        {
            "id": 3,
            "dataset_id": 12,
            "from_user_id": 5,
            "to_user_id": 6,
            "status": "PENDING",
            "message": None,
            "created_at": ago(500),
            "resolved_at": None,
        },
    ]


def metrics_rows():
    return [
        {
            "hubfile_id": 1,
            "extracted_at": ago(299),
            "extractor_version": "1.0",
            "features": 2,
            "satisfiable": True,
            "configurations": 2.0,
        },
        {
            "hubfile_id": 12,
            "extracted_at": ago(589),
            "extractor_version": "1.0",
            "features": 3,
            "satisfiable": True,
            "configurations": 4.0,
        },
    ]


def usage_rows():
    return {
        "ds_view_record": [
            {
                "id": 1,
                "user_id": None,
                "dataset_id": 1,
                "view_date": ago(3),
                "view_cookie": "c1",
            },
            {
                "id": 2,
                "user_id": 2,
                "dataset_id": 1,
                "view_date": ago(2),
                "view_cookie": "c2",
            },
            # Its owner's own visit, a draft's, the seed's, and two more on
            # the day of 1: one by the same browser, one by bob.
            {
                "id": 3,
                "user_id": 1,
                "dataset_id": 1,
                "view_date": ago(2),
                "view_cookie": "c5",
            },
            {
                "id": 4,
                "user_id": None,
                "dataset_id": 5,
                "view_date": ago(2),
                "view_cookie": "c6",
            },
            {
                "id": 5,
                "user_id": None,
                "dataset_id": 12,
                "view_date": ago(2),
                "view_cookie": "c7",
            },
            {
                "id": 6,
                "user_id": None,
                "dataset_id": 1,
                "view_date": ago(3, hours=-2),
                "view_cookie": "c1",
            },
            {
                "id": 7,
                "user_id": 2,
                "dataset_id": 1,
                "view_date": ago(3, hours=-5),
                "view_cookie": "c9",
            },
        ],
        "ds_download_record": [
            {
                "id": 1,
                "user_id": None,
                "dataset_id": None,
                "download_date": ago(3),
                "download_cookie": "c3",
            },
        ],
        "hubfile_view_record": [
            {
                "id": 1,
                "user_id": None,
                "file_id": 1,
                "view_date": None,
                "view_cookie": None,
            },
        ],
        "hubfile_download_record": [
            {
                "id": 1,
                "user_id": 2,
                "file_id": 1,
                "download_date": ago(1),
                "download_cookie": "c4",
            },
        ],
        "statistics": [
            {
                "id": 1,
                "datasets_viewed": 10,
                "feature_models_viewed": 20,
                "datasets_downloaded": 3,
                "feature_models_downloaded": 4,
                "datasets_counter": 12,
                "feature_models_counter": 17,
            },
        ],
        # A mapping, one that leads to it, a cycle, one that leads nowhere,
        # and one the first hides (v2.12 found the first).
        "doi_mapping": [
            {"id": i, "dataset_doi_old": old, "dataset_doi_new": new}
            for i, old, new in (
                (1, "10.5281/zenodo.999", "10.5281/zenodo.1001"),
                (2, "10.5281/zenodo.998", "10.5281/zenodo.999"),
                (3, "10.5281/zenodo.3001", "10.5281/zenodo.3002"),
                (4, "10.5281/zenodo.3002", "10.5281/zenodo.3001"),
                (5, "10.5281/zenodo.997", "10.5281/zenodo.4040"),
                (6, "10.5281/zenodo.999", "10.5281/zenodo.1003"),
            )
        ],
        "hubfile_factlabel": [{"hubfile_id": 1, "factlabel_json": "{}"}],
    }


# What the enrichment of §4.3 fetched from Zenodo (MIG-06), as
# uvlhub_migration_inputs.zenodo_snapshot keeps it: the record of the
# deleted dataset 290, which dates its tombstone.
ORPHAN_RECORD = {
    "id": 2001,
    "doi": ORPHAN_DOI,
    "created": "2025-03-01T10:00:00.000000+00:00",
    "metadata": {"publication_date": "2025-03-02", "title": "Deleted, with a DOI"},
}


# And the record of dataset 3, which gives the concept DOI v2.12 did not keep
# (§4.3, CT-4).
DATASET_3_CONCEPT = "10.5281/zenodo.1004"
DATASET_3_RECORD = {
    "id": 1005,
    "doi": "10.5281/zenodo.1005",
    "conceptdoi": DATASET_3_CONCEPT,
    "created": "2025-06-01T10:00:00.000000+00:00",
    "metadata": {"publication_date": "2025-06-01", "title": "Sync pending"},
}


def zenodo_snapshot():
    found = []
    for record in (ORPHAN_RECORD, DATASET_3_RECORD):
        text = json.dumps(record, sort_keys=True)
        found.append(
            {
                "deposition_id": record["id"],
                "record": text,
                "sha256": sha256(text.encode("utf-8")),
            }
        )
    return found


def zenodo_files():
    """What ``zenodo-files`` keeps for the published file the mirror holds
    otherwise (§6.2 step 5): file 4 of dataset 3, as Zenodo published it,
    the bytes its row says."""
    content = content_of(4)
    return [
        {
            "hubfile_id": 4,
            "dataset_id": 3,
            "deposition_id": 1005,
            "doi": "10.5281/zenodo.1005",
            "path": "drift.uvl",
            "origin": "file",
            "zenodo_key": "drift.uvl",
            "zip_entry": None,
            "zenodo_md5": md5(content),
            "size": len(content),
            "md5": md5(content),
            "sha256": sha256(content),
            "content": content,
            "status": "ok",
        }
    ]


# The counters a dump carries, ahead of the rows (§4.1).
COUNTERS = {"user": 40, "external_identity": 50, "datasets": 30, "hubfiles": 25}


def build(connection, schema: str, head: str = "e5f6a7b8c9d0") -> None:
    """Create ``schema`` as a v2.12 database at ``head`` with every row
    above, plus a trigger and a view, which should not exist (P-28)."""
    connection.exec_driver_sql(f"DROP DATABASE IF EXISTS `{schema}`")
    connection.exec_driver_sql(f"CREATE DATABASE `{schema}`")
    connection.exec_driver_sql(f"USE `{schema}`")
    for statement in v2_12_schema.statements():
        connection.exec_driver_sql(statement)
    metadata = sa.MetaData()
    metadata.reflect(bind=connection, schema=schema)
    tables = {table.name: table for table in metadata.tables.values()}
    metas, datasets, fms, files, authors, metrics = content_rows()
    connection.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0")
    for name, rows in [
        ("user", users()),
        ("user_profile", profiles()),
        ("external_identity", external_identities()),
        ("orcid", orcids()),
        ("github", githubs()),
        ("api_keys", api_keys()),
        ("reset_token", reset_tokens()),
        ("ds_metrics", metrics),
        ("ds_meta_data", metas),
        ("datasets", datasets),
        ("author", authors),
        ("feature_model", fms),
        ("hubfiles", files),
        ("hubfile_metrics", metrics_rows()),
        ("dataset_rating", ratings()),
        ("dataset_transfer_request", transfers()),
        *usage_rows().items(),
        ("alembic_version", [{"version_num": head}]),
    ]:
        connection.execute(tables[name].insert(), rows)
    connection.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1")
    for table, counter in COUNTERS.items():
        connection.exec_driver_sql(f"ALTER TABLE `{table}` AUTO_INCREMENT = {counter}")
    connection.exec_driver_sql(
        "CREATE TRIGGER planted BEFORE UPDATE ON `user` FOR EACH ROW SET NEW.active = 1"
    )
    connection.exec_driver_sql(
        "CREATE VIEW planted_view AS SELECT id, email FROM `user`"
    )
    connection.commit()


def write_mirror(mirror: Path) -> None:
    """v2.12's uploads/ as the operator's rsync leaves it in the mirror:
    every file but the missing one, a mismatch, an orphan, a temporary and
    a derived format."""
    for hubfile_id, (dataset_id, _fm, folder, name, kind) in HUBFILES.items():
        if kind == "missing":
            continue
        owner = DATASETS[dataset_id][0]
        path = mirror / f"user_{owner}" / f"dataset_{dataset_id}" / "uvl"
        if folder:
            path = path.joinpath(*folder.split("/"))
        path.mkdir(parents=True, exist_ok=True)
        content = content_of(hubfile_id)
        if kind == "mismatch":
            content += b"// edited after it was uploaded\n"
        (path / name).write_bytes(content)
    extras = {
        "user_1/dataset_99/uvl/lost.uvl": uvl("Lost"),
        "temp/1/half.uvl": uvl("Half"),
        "user_1/dataset_1/glencoe/model one.json": b"{}",
        "user_2/dataset_3/glencoe/drift.json": b"{}",
    }
    for relative, content in extras.items():
        path = mirror / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
