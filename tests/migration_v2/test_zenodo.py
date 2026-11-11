"""MIG-06: how Zenodo's records are asked for, without asking Zenodo.

The snapshot itself writes into a server's inputs schema; its pieces that
talk to Zenodo are checked here with a fake session.
"""

import requests

from uvlhub_splent.migration_v2 import zenodo


class FakeResponse:
    def __init__(self, status, text="", headers=None):
        self.status_code = status
        self.text = text
        self.headers = headers or {}


class FakeSession:
    def __init__(self, answers):
        self.answers = list(answers)
        self.asked = []

    def get(self, url, headers=None, timeout=None):
        self.asked.append(url)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def no_sleep(_seconds):
    pass


def test_a_record_is_its_text():
    session = FakeSession([FakeResponse(200, '{"doi": "10.5281/zenodo.7"}')])

    assert zenodo.fetch(session, 7, sleep=no_sleep) == (
        200,
        '{"doi": "10.5281/zenodo.7"}',
    )
    assert session.asked == ["https://zenodo.org/api/records/7"]


def test_a_429_and_a_5xx_are_asked_again():
    session = FakeSession(
        [
            FakeResponse(429, headers={"Retry-After": "2"}),
            FakeResponse(502),
            FakeResponse(200, "{}"),
        ]
    )
    waited = []

    assert zenodo.fetch(session, 7, sleep=waited.append) == (200, "{}")
    assert waited[0] == 2.0
    assert len(session.asked) == 3


def test_a_404_or_a_410_is_an_answer_not_a_record():
    for status in (404, 410):
        session = FakeSession([FakeResponse(status)])
        assert zenodo.fetch(session, 7, sleep=no_sleep) == (status, None)
        assert len(session.asked) == 1


def test_a_connection_that_keeps_failing_raises():
    session = FakeSession([requests.ConnectionError("down")] * (zenodo.RETRIES + 1))

    try:
        zenodo.fetch(session, 7, sleep=no_sleep)
    except requests.ConnectionError:
        pass
    else:
        raise AssertionError("the last failure should raise")


def test_the_summary_lists_what_did_not_come():
    outcome = zenodo.Outcome(kept=2, already=1, missing={9: 404}, failed={3: "down"})

    assert zenodo.summary(outcome) == {
        "kept": 2,
        "kept_already": 1,
        "missing": {"9": 404},
        "failed": {"3": "down"},
    }


class EveryRecord:
    """Zenodo as the snapshot sees it: one record, and 404 for the rest."""

    def __init__(self, records):
        self.records = records
        self.asked = []

    def get(self, url, headers=None, timeout=None):
        self.asked.append(url)
        deposition_id = int(url.rsplit("/", 1)[1])
        text = self.records.get(deposition_id)
        return FakeResponse(200, text) if text else FakeResponse(404)


def test_the_snapshot_keeps_each_record_once(migrated, root_engine):
    from uvlhub_splent.migration_v2.db import make_engine

    schema = "iso_zenodo_snapshot_inputs"
    server = migrated.params.server
    engine = make_engine(server.host, server.port, server.user, server.password)
    session = EveryRecord({1001: '{"doi": "10.5281/zenodo.1001"}'})
    try:
        outcome = zenodo.snapshot(
            engine,
            migrated.params.source_schema,
            schema,
            session=session,
            sleep=no_sleep,
            echo=lambda _line: None,
        )
        again = zenodo.snapshot(
            engine,
            migrated.params.source_schema,
            schema,
            session=EveryRecord({}),
            sleep=no_sleep,
            echo=lambda _line: None,
        )
        with engine.connect() as connection:
            kept = (
                connection.exec_driver_sql(
                    f"SELECT deposition_id FROM `{schema}`.zenodo_snapshot"
                )
                .scalars()
                .all()
            )
    finally:
        engine.dispose()
        with root_engine.connect() as connection:
            connection.exec_driver_sql(f"DROP DATABASE IF EXISTS `{schema}`")
            connection.commit()

    assert outcome.kept == 1 and kept == [1001]
    assert 404 in outcome.missing.values()
    # A record kept is not asked for again; the ones that were not are.
    assert again.already == 1 and again.kept == 0
