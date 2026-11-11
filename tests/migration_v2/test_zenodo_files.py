"""§6.2 step 5: how the files of published datasets come back from Zenodo,
without asking Zenodo.

Where a record keeps a file, how a download is checked and cached, and what
zenodo_files holds once ``zenodo-files`` ran on the dirty v2.12; what E8
does with it is test_pipeline's.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from collections import Counter

import pytest
import requests
import sqlalchemy as sa

from uvlhub.migration_v2 import zenodo, zenodo_files
from uvlhub.migration_v2.db import make_engine
from uvlhub.migration_v2.zenodo_files import (
    ARCHIVE,
    LOOSE,
    Wanted,
    ZenodoFile,
    locate,
    record_files,
    zip_entry,
)

from . import synthetic


def md5(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


class FakeResponse:
    def __init__(self, status, content=b"", headers=None, text=""):
        self.status_code = status
        self.content = content
        self.text = text
        self.headers = headers or {}
        self.closed = False

    def iter_content(self, _size):
        yield self.content[: len(self.content) // 2]
        yield self.content[len(self.content) // 2 :]

    def close(self):
        self.closed = True


class FakeSession:
    """Answers by URL; ``asked`` keeps every request."""

    def __init__(self, answers):
        self.answers = {url: list(found) for url, found in answers.items()}
        self.asked = []

    def get(self, url, headers=None, timeout=None, stream=False):
        self.asked.append(url)
        found = self.answers.get(url)
        if not found:
            raise AssertionError(f"nothing should ask for {url}")
        answer = found.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def no_sleep(_seconds):
    pass


def wanted(name="model.uvl", folder="", dataset_id=7):
    return Wanted(1, dataset_id, 1007, "10.5281/zenodo.1007", folder, name, "mismatch")


def zenodo_file(key, content=b"x"):
    return ZenodoFile(key, md5(content), len(content), f"https://zenodo.org/f/{key}")


# ── Where a record keeps a file ──────────────────────────────────────────


def test_a_records_files_are_read_in_both_shapes():
    entry = {
        "key": "a.uvl",
        "size": 3,
        "checksum": "md5:" + "0" * 32,
        "links": {"self": "https://zenodo.org/api/records/9/files/a.uvl/content"},
    }
    listed = record_files({"files": [entry]}, 9)
    entries = record_files({"files": {"entries": {"a.uvl": entry}}}, 9)

    assert (
        listed
        == entries
        == [
            ZenodoFile(
                "a.uvl",
                "0" * 32,
                3,
                "https://zenodo.org/api/records/9/files/a.uvl/content",
            )
        ]
    )


def test_a_file_is_downloaded_from_zenodo_only():
    entry = {
        "key": "a b.uvl",
        "checksum": "md5:" + "1" * 32,
        "links": {"self": "https://elsewhere.example/a.uvl"},
    }
    (found,) = record_files({"files": [entry]}, 9)

    assert found.url == "https://zenodo.org/api/records/9/files/a%20b.uvl/content"


def test_a_file_without_an_md5_is_not_taken():
    entry = {"key": "a.uvl", "checksum": "sha256:" + "1" * 64}

    assert record_files({"files": [entry]}, 9) == []


def test_a_loose_file_is_found_by_its_name_or_its_path():
    by_name = zenodo_file("model.uvl")
    by_path = zenodo_file("sub/model.uvl")

    assert locate([by_name], wanted(), Counter({"model.uvl": 1})) == (
        LOOSE,
        by_name,
        None,
    )
    assert locate(
        [by_name, by_path], wanted(folder="sub"), Counter({"model.uvl": 2})
    ) == (LOOSE, by_path, None)


def test_a_name_two_files_of_the_dataset_share_is_not_taken_alone():
    assert locate(
        [zenodo_file("model.uvl")], wanted(folder="sub"), Counter({"model.uvl": 2})
    ) == (None, zenodo_files.AMBIGUOUS, None)


def test_otherwise_the_file_is_looked_for_in_the_datasets_archive():
    archive = zenodo_file("dataset_7.zip")
    other = zenodo_file("notes.zip")

    assert locate([other, archive], wanted(folder="sub"), Counter()) == (
        ARCHIVE,
        archive,
        "sub/model.uvl",
    )
    # The only archive of a record, whatever its name.
    assert locate([other], wanted(), Counter())[:2] == (ARCHIVE, other)
    assert locate([other, zenodo_file("more.zip")], wanted(), Counter()) == (
        None,
        zenodo_files.NOT_IN_RECORD,
        None,
    )


def archive_with(tmp_path, entries: dict[str, bytes]):
    path = tmp_path / "archive.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return path


def test_an_archives_entry_is_uvl_its_path_or_the_one_that_ends_so(tmp_path):
    path = archive_with(
        tmp_path,
        {
            "uvl/sub/a.uvl": b"first",
            "b.uvl": b"second",
            "dataset_7/c.uvl": b"third",
            "one/d.uvl": b"x",
            "two/d.uvl": b"y",
        },
    )

    assert zip_entry(path, "sub/a.uvl") == ("ok", b"first", "uvl/sub/a.uvl")
    assert zip_entry(path, "b.uvl") == ("ok", b"second", "b.uvl")
    assert zip_entry(path, "c.uvl") == ("ok", b"third", "dataset_7/c.uvl")
    assert zip_entry(path, "d.uvl") == (zenodo_files.NOT_IN_ZIP, None, None)
    assert zip_entry(path, "e.uvl") == (zenodo_files.NOT_IN_ZIP, None, None)


def test_an_entry_is_found_whatever_the_normal_form_of_its_name(tmp_path):
    decomposed = "café.uvl"
    path = archive_with(tmp_path, {f"uvl/{decomposed}": b"bytes"})

    assert zip_entry(path, "café.uvl")[:2] == ("ok", b"bytes")


# ── Downloads ────────────────────────────────────────────────────────────


def test_a_download_is_kept_only_when_it_is_zenodos_md5(tmp_path):
    item = zenodo_file("a.uvl", b"the bytes")
    good = FakeSession({item.url: [FakeResponse(200, b"the bytes")]})
    bad = FakeSession({item.url: [FakeResponse(200, b"other bytes")]})

    assert zenodo_files.download(good, item, tmp_path / "a", sleep=no_sleep) == "ok"
    assert (tmp_path / "a").read_bytes() == b"the bytes"
    assert zenodo_files.download(bad, item, tmp_path / "b", sleep=no_sleep) == (
        zenodo_files.MD5_MISMATCH
    )
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a"]


def test_a_download_waits_as_zenodo_asks(tmp_path):
    item = zenodo_file("a.uvl", b"bytes")
    session = FakeSession(
        {
            item.url: [
                FakeResponse(429, headers={"Retry-After": "7"}),
                FakeResponse(503),
                requests.ConnectionError("down"),
                FakeResponse(200, b"bytes"),
            ]
        }
    )
    waited = []

    assert zenodo_files.download(
        session, item, tmp_path / "a", sleep=waited.append
    ) == ("ok")
    assert waited[0] == 7.0
    assert len(session.asked) == 4


def test_a_download_zenodo_refuses_says_so(tmp_path):
    item = zenodo_file("a.uvl", b"bytes")
    session = FakeSession({item.url: [FakeResponse(404)]})

    assert zenodo_files.download(session, item, tmp_path / "a", sleep=no_sleep) == (
        "fetch_failed_404"
    )


# ── zenodo-files on the dirty v2.12 ──────────────────────────────────────

# Dataset 3 is published (10.5281/zenodo.1005) and the mirror holds its file
# 4 with other bytes; Zenodo's record has the ones its row says.
RECORD = {
    "id": 1005,
    "doi": "10.5281/zenodo.1005",
    "files": [
        {
            "key": "drift.uvl",
            "size": len(synthetic.content_of(4)),
            "checksum": "md5:" + md5(synthetic.content_of(4)),
            "links": {
                "self": "https://zenodo.org/api/records/1005/files/drift.uvl/content"
            },
        }
    ],
}
FILE_URL = RECORD["files"][0]["links"]["self"]


@pytest.fixture
def inputs_schema(migrated, root_engine):
    """An inputs schema of the test's own, beside the rehearsal's."""
    schema = "iso_zenodo_files_inputs"
    yield schema
    with root_engine.connect() as connection:
        connection.exec_driver_sql(f"DROP DATABASE IF EXISTS `{schema}`")
        connection.commit()


def migrator(migrated):
    server = migrated.params.server
    return make_engine(server.host, server.port, server.user, server.password)


def kept(engine, schema):
    with engine.connect() as connection:
        return [
            dict(row)
            for row in connection.execute(
                sa.text(f"SELECT * FROM `{schema}`.zenodo_files ORDER BY hubfile_id")
            ).mappings()
        ]


def test_zenodo_files_keeps_the_published_files_zenodo_gives_back(
    migrated, store, inputs_schema, tmp_path
):
    engine = migrator(migrated)
    session = FakeSession(
        {
            zenodo.RECORDS_URL.format(id=1005): [
                FakeResponse(200, text=json.dumps(RECORD))
            ],
            FILE_URL: [FakeResponse(200, synthetic.content_of(4))],
        }
    )
    cache = tmp_path / "cache"

    outcome = zenodo_files.fetch_files(
        engine,
        migrated.params.source_schema,
        inputs_schema,
        store / ".legacy_mirror",
        cache,
        session=session,
        sleep=no_sleep,
        echo=lambda _line: None,
    )

    # File 6 is missing too, but its dataset is a draft (§6.2 step 6).
    assert zenodo_files.summary(outcome) == {
        "wanted": 1,
        "recovered": {"file": 1},
        "not_recovered": {},
        "downloaded": 1,
        "from_cache": 0,
    }
    (row,) = kept(engine, inputs_schema)
    content = synthetic.content_of(4)
    assert row == {
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
        "sha256": hashlib.sha256(content).hexdigest(),
        "content": content,
        "status": "ok",
    }

    # A second run asks Zenodo for the record only: the file is in the cache.
    again = FakeSession(
        {
            zenodo.RECORDS_URL.format(id=1005): [
                FakeResponse(200, text=json.dumps(RECORD))
            ]
        }
    )
    outcome = zenodo_files.fetch_files(
        engine,
        migrated.params.source_schema,
        inputs_schema,
        store / ".legacy_mirror",
        cache,
        session=again,
        sleep=no_sleep,
        echo=lambda _line: None,
    )
    engine.dispose()
    assert (outcome.downloaded, outcome.cached) == (0, 1)
    assert again.asked == [zenodo.RECORDS_URL.format(id=1005)]


def test_zenodo_files_says_why_a_file_does_not_come(
    migrated, store, inputs_schema, tmp_path
):
    engine = migrator(migrated)
    other = dict(RECORD, doi="10.5281/zenodo.9999")
    session = FakeSession(
        {
            zenodo.RECORDS_URL.format(id=1005): [
                FakeResponse(200, text=json.dumps(other))
            ]
        }
    )

    outcome = zenodo_files.fetch_files(
        engine,
        migrated.params.source_schema,
        inputs_schema,
        store / ".legacy_mirror",
        tmp_path / "cache",
        session=session,
        sleep=no_sleep,
        echo=lambda _line: None,
    )
    rows = kept(engine, inputs_schema)
    engine.dispose()

    assert dict(outcome.failed) == {zenodo_files.RECORD_INVALID: [4]}
    assert [(r["hubfile_id"], r["status"], r["content"]) for r in rows] == [
        (4, zenodo_files.RECORD_INVALID, None)
    ]


def test_an_archive_in_the_cache_is_read_again_without_asking(tmp_path):
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("uvl/a.uvl", b"bytes")
    path = tmp_path / md5(content.getvalue())
    path.write_bytes(content.getvalue())

    assert zenodo_files.md5_of(path) == path.name
    assert zip_entry(path, "a.uvl")[:2] == ("ok", b"bytes")


# ── What E8 does with them ───────────────────────────────────────────────


def a_row(status, checksum, size=5, algo=None):
    from types import SimpleNamespace

    return SimpleNamespace(
        id=4,
        dataset_id=3,
        storage_status=status,
        checksum=checksum,
        checksum_algo=algo,
        size=size,
    )


GIVEN = {
    "deposition_id": 1005,
    "origin": "file",
    "zenodo_key": "a.uvl",
    "zip_entry": None,
}


def test_a_missing_file_is_restored_with_its_rows_algorithm():
    from uvlhub.migration_v2.files import plan_repair

    content = b"zenodo"
    repair = plan_repair(a_row("missing", md5(b"old"), 3, "md5"), GIVEN, content, None)

    assert (repair["outcome"], repair["checksum"], repair["checksum_algo"]) == (
        "restored",
        md5(content),
        "md5",
    )
    assert (repair["old_size"], repair["old_checksum"]) == (3, md5(b"old"))
    assert repair["content_sha256"] == hashlib.sha256(content).hexdigest()


def test_bytes_the_mirror_has_already_mend_the_row_only():
    from uvlhub.migration_v2.files import plan_repair

    content = b"zenodo"
    sha256 = hashlib.sha256(content).hexdigest()
    fixed = plan_repair(a_row("mismatch", "f" * 64, 9), GIVEN, content, sha256)
    replaced = plan_repair(a_row("mismatch", "f" * 64, 9), GIVEN, content, "0" * 64)

    assert (fixed["outcome"], fixed["size"], fixed["checksum"]) == (
        "row_fixed",
        len(content),
        sha256,
    )
    assert replaced["outcome"] == "replaced"


def test_a_checksum_of_no_algorithm_becomes_a_sha256():
    from uvlhub.migration_v2.files import checksum_in

    assert checksum_in(None, b"x") == (hashlib.sha256(b"x").hexdigest(), "sha256")
    assert checksum_in("md5", b"x") == (md5(b"x"), "md5")
