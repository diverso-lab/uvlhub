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
