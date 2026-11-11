"""§6.2 step 5: the files of published datasets Zenodo gives back.

A file of a published dataset that the mirror of v2.12's uploads/ does not
have (missing), or has with other bytes than its row says (mismatch), is
fetched from the Zenodo record its DOI cites, and from nowhere else: the
bytes Zenodo published are the ones the DOI stands for, so for a published
dataset they are authoritative. Only those records are asked for, and only
the files wanted are downloaded:

- a loose file of the record named as the hubfile (uvlhub published one
  file per model until 2025-07-28), or named by its relative path;
- else the entry ``uvl/<relative_path>`` of the record's
  ``dataset_<id>.zip`` (one archive per dataset since then), or of the
  record's only archive when it has no such one (a dataset deposited as one
  archive of another name), where the entry may also be at
  ``<relative_path>`` or under one folder, as long as one entry only ends
  so.

What is downloaded is checked against the ``md5:`` Zenodo publishes for it
and kept in a cache folder, by deposition and md5, so a rehearsal that
starts over asks Zenodo for nothing it has. The bytes of each file go to
``uvlhub_migration_inputs.zenodo_files`` with their size, md5 and sha256,
or the reason they could not be had: an input, as zenodo_snapshot is
(§3.5), which E8 reads to store them (files.repair_from_zenodo). The
records come from zenodo_snapshot when it has them, and are fetched
otherwise, never kept there (that is ``zenodo-snapshot``'s).

Like ``zenodo-snapshot``, it runs from the host of operation, never from
staging (R-07), sequentially, at a pace Zenodo takes, and a 429 or a 5xx
waits (its Retry-After when it gives one) and asks again.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import unicodedata
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

import requests
import sqlalchemy as sa
from splent_io.splent_feature_hubfile.legacy import MISMATCH, MISSING, verify

from uvlhub.migration_v2 import db as dbm
from uvlhub.migration_v2 import ledger, rules, zenodo
from uvlhub.migration_v2.files import legacy_path

FILE_URL = "https://zenodo.org/api/records/{id}/files/{key}/content"
#: Where a file may be downloaded from: Zenodo itself, whatever a record says.
ZENODO = "https://zenodo.org/"

#: Seconds between two downloads.
PACE = 0.4

#: A ZIP larger than this is not downloaded.
MAX_DOWNLOAD = 2 * 1024**3

#: The largest file zenodo_files keeps: MariaDB's max_allowed_packet is 16 MiB
#: by default, and a row travels in one packet.
MAX_CONTENT = 15 * 1024**2

CHUNK = 1024 * 1024

OK = "ok"
# Why a file could not be had, as zenodo_files.status says it.
NO_RECORD = "no_record"
RECORD_INVALID = "record_invalid"
NOT_IN_RECORD = "not_in_record"
AMBIGUOUS = "ambiguous_name"
MD5_MISMATCH = "md5_mismatch"
NOT_IN_ZIP = "not_in_zip"
TOO_LARGE = "too_large"
FETCH_FAILED = "fetch_failed"

LOOSE, ARCHIVE = "file", "zip"

# zenodo_files as this module writes it; an older table is refused.
COLUMNS = {
    "hubfile_id",
    "dataset_id",
    "deposition_id",
    "doi",
    "path",
    "origin",
    "zenodo_key",
    "zip_entry",
    "zenodo_md5",
    "size",
    "md5",
    "sha256",
    "content",
    "status",
}


@dataclass(frozen=True)
class Wanted:
    """A file of a published dataset the mirror lacks or has otherwise."""

    hubfile_id: int
    dataset_id: int
    deposition_id: int
    doi: str
    directory_path: str
    name: str
    # What the mirror has of it: missing or mismatch.
    status: str

    @property
    def relative_path(self) -> str:
        return (
            f"{self.directory_path}/{self.name}" if self.directory_path else self.name
        )


@dataclass(frozen=True)
class ZenodoFile:
    key: str
    md5: str
    size: int | None
    url: str


@dataclass
class Outcome:
    wanted: int = 0
    recovered: Counter = field(default_factory=Counter)  # origin -> files
    failed: dict = field(default_factory=lambda: defaultdict(list))  # why -> ids
    downloaded: int = 0
    cached: int = 0


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text or "")


def wanted_files(connection, source_schema: str, mirror: Path) -> list[Wanted]:
    """The files of the source's published datasets (a DOI, of their own
    deposition, C-30) the mirror lacks or holds with other bytes than their
    row says, as hubfile's storage-migrate tells them (legacy.verify)."""
    rows = connection.execute(
        sa.text(
            "SELECT h.id, h.dataset_id, h.name, h.directory_path, h.checksum, "
            "h.size, d.user_id, m.dataset_doi, m.deposition_id "
            f"FROM {dbm.qualified(source_schema, 'hubfiles')} h "
            f"JOIN {dbm.qualified(source_schema, 'datasets')} d ON d.id = h.dataset_id "
            f"JOIN {dbm.qualified(source_schema, 'ds_meta_data')} m "
            "ON m.id = d.ds_meta_data_id ORDER BY h.id"
        )
    ).all()
    wanted = []
    for row in rows:
        doi = (row.dataset_doi or "").strip()
        if not doi or not rules.doi_is_of_deposition(doi, row.deposition_id):
            continue
        path = mirror / legacy_path(row)
        if not path.is_file():
            status = MISSING
        else:
            status, _algo, _sha256 = verify(str(path), row.size, row.checksum)
            if status != MISMATCH:
                continue
        wanted.append(
            Wanted(
                hubfile_id=row.id,
                dataset_id=row.dataset_id,
                deposition_id=int(row.deposition_id),
                doi=doi,
                directory_path=row.directory_path or "",
                name=row.name,
                status=status,
            )
        )
    return wanted


def record_files(record: dict, deposition_id: int) -> list[ZenodoFile]:
    """The files of a Zenodo record that publish an md5, in the shape of
    /api/records (a list) or of InvenioRDM's own (``entries``)."""
    found = record.get("files") or []
    if isinstance(found, dict):
        entries = found.get("entries") or {}
        found = list(entries.values()) if isinstance(entries, dict) else entries
    files = []
    for entry in found:
        if not isinstance(entry, dict):
            continue
        key = entry.get("key") or entry.get("filename")
        algo, _, digest = (entry.get("checksum") or "").partition(":")
        if not key or algo.lower() != "md5" or len(digest) != 32:
            continue
        links = entry.get("links") or {}
        url = links.get("self") or links.get("content") or ""
        if not url.startswith(ZENODO):
            url = FILE_URL.format(id=deposition_id, key=quote(key, safe=""))
        files.append(ZenodoFile(key, digest.lower(), entry.get("size"), url))
    return files


def locate(files: list[ZenodoFile], wanted: Wanted, names: Counter):
    """(origin, the Zenodo file, the path to look for in it) where
    ``wanted`` is, or (None, the reason, None). ``names`` counts the
    dataset's files by name: a loose file is taken by name only when one
    file of the dataset has it."""
    by_key = {_nfc(f.key): f for f in files}
    if wanted.directory_path:
        loose = by_key.get(_nfc(wanted.relative_path))
        if loose is not None:
            return LOOSE, loose, None
    loose = by_key.get(_nfc(wanted.name))
    if loose is not None:
        if names[wanted.name] > 1:
            return None, AMBIGUOUS, None
        return LOOSE, loose, None
    archive = by_key.get(f"dataset_{wanted.dataset_id}.zip")
    if archive is None:
        archives = [f for f in files if f.key.lower().endswith(".zip")]
        archive = archives[0] if len(archives) == 1 else None
    if archive is not None:
        return ARCHIVE, archive, wanted.relative_path
    return None, NOT_IN_RECORD, None


def md5_of(path: Path) -> str:
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(session, item: ZenodoFile, target: Path, sleep=time.sleep) -> str:
    """Download ``item`` to ``target``, checked against Zenodo's md5: OK, or
    why not. Nothing is left at ``target`` unless it is the file."""
    part = target.with_name(target.name + ".part")
    wait = zenodo.PACE
    for attempt in range(zenodo.RETRIES + 1):
        try:
            response = session.get(item.url, stream=True, timeout=60)
        except requests.RequestException:
            if attempt == zenodo.RETRIES:
                return FETCH_FAILED
            sleep(wait)
            wait *= 2
            continue
        if response.status_code == 429 or response.status_code >= 500:
            response.close()
            if attempt == zenodo.RETRIES:
                return FETCH_FAILED
            retry_after = response.headers.get("Retry-After")
            sleep(float(retry_after) if retry_after and retry_after.isdigit() else wait)
            wait *= 2
            continue
        if response.status_code != 200:
            response.close()
            return f"{FETCH_FAILED}_{response.status_code}"
        digest, size = hashlib.md5(), 0
        try:
            with open(part, "wb") as out:
                os.chmod(part, 0o600)
                for chunk in response.iter_content(CHUNK):
                    size += len(chunk)
                    if size > MAX_DOWNLOAD:
                        raise OverflowError
                    digest.update(chunk)
                    out.write(chunk)
        except OverflowError:
            part.unlink(missing_ok=True)
            return TOO_LARGE
        except requests.RequestException:
            part.unlink(missing_ok=True)
            if attempt == zenodo.RETRIES:
                return FETCH_FAILED
            sleep(wait)
            wait *= 2
            continue
        finally:
            response.close()
        if digest.hexdigest() != item.md5:
            part.unlink(missing_ok=True)
            return MD5_MISMATCH
        os.replace(part, target)
        return OK
    return FETCH_FAILED


def zip_entry(archive: Path, relative_path: str):
    """(OK, the bytes, the entry) of the file at ``relative_path`` in
    ``archive``, or (why not, None, None): the entry ``uvl/<relative_path>``
    uvlhub writes, else ``<relative_path>``, else the one entry that ends
    with ``/<relative_path>``, each compared as written or in NFC."""
    wanted = _nfc(relative_path)
    try:
        with zipfile.ZipFile(archive) as opened:
            files = {
                _nfc(info.filename): info
                for info in opened.infolist()
                if not info.is_dir()
            }
            info = files.get(f"uvl/{wanted}") or files.get(wanted)
            if info is None:
                ending = [i for name, i in files.items() if name.endswith(f"/{wanted}")]
                info = ending[0] if len(ending) == 1 else None
            if info is None:
                return NOT_IN_ZIP, None, None
            if info.file_size > MAX_CONTENT:
                return TOO_LARGE, None, info.filename
            return OK, opened.read(info), info.filename
    except zipfile.BadZipFile:
        return NOT_IN_ZIP, None, None


def check_table(connection, schema: str) -> None:
    """Refuse a zenodo_files made before it held the files themselves."""
    have = set(
        connection.execute(
            sa.text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = :s AND table_name = 'zenodo_files'"
            ),
            {"s": schema},
        ).scalars()
    )
    if have != COLUMNS:
        raise RuntimeError(
            f"{schema}.zenodo_files is not the table this migrator writes "
            f"(it has {', '.join(sorted(have))}); drop it, it is made again"
        )


def snapshots(connection, table) -> dict[int, dict]:
    """The records zenodo_snapshot keeps whole, by deposition."""
    found = {}
    for row in connection.execute(sa.select(table)).mappings():
        text = row["record"] or ""
        if hashlib.sha256(text.encode("utf-8")).hexdigest() == row["sha256"]:
            try:
                found[row["deposition_id"]] = json.loads(text)
            except ValueError:
                continue
    return found


def fetch_files(
    engine,
    source_schema: str,
    inputs_schema: str,
    mirror: Path,
    cache: Path,
    *,
    session=None,
    sleep=time.sleep,
    echo=print,
) -> Outcome:
    """Fill zenodo_files with every file of a published dataset that the
    mirror lacks or holds otherwise, as Zenodo gives it, or why not."""
    outcome = Outcome()
    session = session or requests.Session()
    cache.mkdir(parents=True, exist_ok=True)
    os.chmod(cache, 0o700)
    # ensure_inputs commits on its connection: no transaction of engine.begin()
    # around it.
    with engine.connect() as connection:
        tables = ledger.ensure_inputs(connection, inputs_schema)
        check_table(connection, inputs_schema)
        wanted = wanted_files(connection, source_schema, mirror)
        records = snapshots(connection, tables["zenodo_snapshot"])
        names = defaultdict(Counter)
        for row in connection.execute(
            sa.text(
                "SELECT dataset_id, name FROM "
                f"{dbm.qualified(source_schema, 'hubfiles')}"
            )
        ):
            names[row.dataset_id][row.name] += 1
        connection.rollback()
    outcome.wanted = len(wanted)
    echo(f"Zenodo files: {len(wanted)} file(s) of published datasets to recover.")

    by_deposition = defaultdict(list)
    for item in wanted:
        by_deposition[item.deposition_id].append(item)
    rows, checked = [], set()
    for deposition_id, items in sorted(by_deposition.items()):
        record = records.get(deposition_id)
        if record is None:
            status, text = zenodo.fetch(session, deposition_id, sleep=sleep)
            sleep(zenodo.PACE)
            record = json.loads(text) if status == 200 and text else None
        if record is None:
            rows += [_failed(item, NO_RECORD) for item in items]
            continue
        if (record.get("doi") or "").strip().lower() != items[0].doi.lower():
            rows += [_failed(item, RECORD_INVALID) for item in items]
            continue
        files = record_files(record, deposition_id)
        folder = cache / str(deposition_id)
        for item in sorted(items, key=lambda i: i.hubfile_id):
            origin, found, inside = locate(files, item, names[item.dataset_id])
            if origin is None:
                rows.append(_failed(item, found))
                continue
            folder.mkdir(exist_ok=True)
            os.chmod(folder, 0o700)
            target, entry = folder / found.md5, None
            if target in checked:
                pass
            elif target.is_file() and md5_of(target) == found.md5:
                outcome.cached += 1
                checked.add(target)
            else:
                status = download(session, found, target, sleep=sleep)
                sleep(PACE)
                if status != OK:
                    rows.append(_failed(item, status, origin, found))
                    continue
                outcome.downloaded += 1
                checked.add(target)
            if origin == ARCHIVE:
                why, content, entry = zip_entry(target, inside)
            elif target.stat().st_size > MAX_CONTENT:
                why, content = TOO_LARGE, None
            else:
                why, content = OK, target.read_bytes()
            if content is None:
                rows.append(_failed(item, why, origin, found, entry))
                continue
            rows.append(
                dict(
                    _row(item, origin, found, entry),
                    size=len(content),
                    md5=hashlib.md5(content).hexdigest(),
                    sha256=hashlib.sha256(content).hexdigest(),
                    content=content,
                    status=OK,
                )
            )
    table = tables["zenodo_files"]
    with engine.begin() as connection:
        connection.execute(table.delete())
        for row in sorted(rows, key=lambda r: r["hubfile_id"]):
            connection.execute(table.insert().values(**row))
    for row in rows:
        if row["status"] == OK:
            outcome.recovered[row["origin"]] += 1
        else:
            outcome.failed[row["status"]].append(row["hubfile_id"])
    return outcome


def _row(item: Wanted, origin=None, found=None, entry=None) -> dict:
    return {
        "hubfile_id": item.hubfile_id,
        "dataset_id": item.dataset_id,
        "deposition_id": item.deposition_id,
        "doi": item.doi,
        "path": item.relative_path,
        "origin": origin,
        "zenodo_key": found.key if found is not None else None,
        "zip_entry": entry,
        "zenodo_md5": found.md5 if found is not None else None,
    }


def _failed(item: Wanted, why: str, origin=None, found=None, entry=None) -> dict:
    return dict(
        _row(item, origin, found, entry),
        size=None,
        md5=None,
        sha256=None,
        content=None,
        status=why,
    )


def summary(outcome: Outcome) -> dict:
    return {
        "wanted": outcome.wanted,
        "recovered": dict(sorted(outcome.recovered.items())),
        "not_recovered": {
            why: sorted(ids) for why, ids in sorted(outcome.failed.items())
        },
        "downloaded": outcome.downloaded,
        "from_cache": outcome.cached,
    }
