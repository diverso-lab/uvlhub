"""MIG-06: the snapshot of Zenodo's records that E5 reads (§4.3).

For every deposition of the source, Zenodo's public record
(``GET /api/records/<id>``, no token) is kept whole in
``uvlhub_migration_inputs.zenodo_snapshot`` with its sha256, as
``rules.zenodo_dates`` validates it: E5 dates the tombstones of DM-4 with
it, and the final pass reads ``published_at`` and the concept DOIs that
repair the lineages (C-05) from it.

It runs from the host of operation, never from staging (R-07), and before
every rehearsal: an input, not an output, so a run reads the same snapshot
however many times it starts over. A record already kept is fetched again
only with ``refresh``. Zenodo is asked at a pace it takes, and a 429 or a
5xx waits and asks again; a 404 or a 410 is kept as an answer (a record
withdrawn, or a deposition id that is not Zenodo's), not as a record.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field

import requests
import sqlalchemy as sa

from uvlhub_splent.migration_v2 import db as dbm
from uvlhub_splent.migration_v2 import ledger

RECORDS_URL = "https://zenodo.org/api/records/{id}"

#: Seconds between two requests: Zenodo answers 60 a minute to a guest.
PACE = 1.1

#: How many times a 429 or a 5xx is asked again, waiting twice as long each.
RETRIES = 5


@dataclass
class Outcome:
    kept: int = 0
    already: int = 0
    missing: dict = field(default_factory=dict)  # deposition_id -> status
    failed: dict = field(default_factory=dict)  # deposition_id -> error


def depositions(connection, source_schema: str) -> list[int]:
    """The deposition ids of the source, every one of ds_meta_data's."""
    rows = connection.execute(
        sa.text(
            f"SELECT DISTINCT deposition_id FROM {dbm.qualified(source_schema, 'ds_meta_data')} "
            "WHERE deposition_id IS NOT NULL ORDER BY deposition_id"
        )
    )
    return [int(row[0]) for row in rows]


def fetch(session: requests.Session, deposition_id: int, sleep=time.sleep):
    """(status, text) of Zenodo's record of ``deposition_id``."""
    wait = PACE
    for attempt in range(RETRIES + 1):
        try:
            response = session.get(
                RECORDS_URL.format(id=deposition_id),
                headers={"Accept": "application/json"},
                timeout=30,
            )
        except requests.RequestException:
            if attempt == RETRIES:
                raise
            sleep(wait)
            wait *= 2
            continue
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == RETRIES:
                return response.status_code, None
            retry_after = response.headers.get("Retry-After")
            sleep(float(retry_after) if retry_after and retry_after.isdigit() else wait)
            wait *= 2
            continue
        if response.status_code == 200:
            return 200, response.text
        return response.status_code, None
    return None, None


def snapshot(
    engine,
    source_schema: str,
    inputs_schema: str,
    *,
    refresh=False,
    limit=None,
    session=None,
    sleep=time.sleep,
    echo=print,
) -> Outcome:
    """Fetch and keep Zenodo's record of every deposition of the source."""
    outcome = Outcome()
    session = session or requests.Session()
    # ensure_inputs commits on its connection: no transaction of engine.begin()
    # around it.
    with engine.connect() as connection:
        tables = ledger.ensure_inputs(connection, inputs_schema)
        wanted = depositions(connection, source_schema)
        kept = {
            row[0]
            for row in connection.execute(
                sa.select(tables["zenodo_snapshot"].c.deposition_id)
            )
        }
        connection.rollback()
    table = tables["zenodo_snapshot"]
    todo = [d for d in wanted if refresh or d not in kept]
    outcome.already = len(wanted) - len(todo)
    if limit is not None:
        todo = todo[:limit]
    echo(
        f"Zenodo: {len(wanted)} deposition(s), {outcome.already} kept already, {len(todo)} to fetch."
    )
    for index, deposition_id in enumerate(todo, start=1):
        try:
            status, text = fetch(session, deposition_id, sleep=sleep)
        except requests.RequestException as error:
            outcome.failed[deposition_id] = str(error)
            continue
        if status != 200 or text is None:
            outcome.missing[deposition_id] = status
        else:
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            with engine.begin() as connection:
                connection.execute(
                    table.delete().where(table.c.deposition_id == deposition_id)
                )
                connection.execute(
                    table.insert().values(
                        deposition_id=deposition_id, record=text, sha256=digest
                    )
                )
            outcome.kept += 1
        if index % 50 == 0:
            echo(f"  {index}/{len(todo)}")
        sleep(PACE)
    return outcome


def summary(outcome: Outcome) -> dict:
    return {
        "kept": outcome.kept,
        "kept_already": outcome.already,
        "missing": {str(k): v for k, v in sorted(outcome.missing.items())},
        "failed": {str(k): v for k, v in sorted(outcome.failed.items())},
    }


def record_of(text: str) -> dict:
    """A kept record as JSON, for the passes that read it."""
    return json.loads(text)
