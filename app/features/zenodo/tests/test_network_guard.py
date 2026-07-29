"""
The suite must not be able to reach a real service.

On 2026-07-28 a test run published three datasets to production Zenodo and
minted three permanent DOIs. The cause was not a missing mock: a fixture
patched the relay through the shared monkeypatch, so a single undo() inside one
test restored the real functions and the real credentials for everything that
ran afterwards. Any guard that lives at the same level as the code it guards
can be undone the same way, so the transport itself is closed instead.
"""

import http.client
import urllib.request

import pytest
import requests

from app.features.conftest import OutboundHttpBlocked


def test_requests_cannot_reach_the_network():
    with pytest.raises(OutboundHttpBlocked):
        requests.get("https://zenodo.org/api/deposit/depositions", timeout=1)


def test_a_session_cannot_reach_the_network_either():
    """requests.Session is the shape the Zenodo service actually uses."""
    with pytest.raises(OutboundHttpBlocked):
        requests.Session().post("https://zenodo.org/api/deposit/depositions", timeout=1)


def test_urllib_cannot_reach_the_network():
    with pytest.raises(OutboundHttpBlocked):
        urllib.request.urlopen("https://zenodo.org/api/deposit/depositions")


def test_the_lowest_level_client_cannot_reach_the_network():
    with pytest.raises(OutboundHttpBlocked):
        http.client.HTTPConnection("zenodo.org").request("GET", "/api")


def test_the_guard_survives_a_test_undoing_its_own_patches(monkeypatch):
    """The exact shape of the accident: a test undoes the shared monkeypatch.

    The guard owns a different fixture, so undo() here cannot reopen it.
    """
    monkeypatch.setattr(requests, "codes", None)
    monkeypatch.undo()

    with pytest.raises(OutboundHttpBlocked):
        requests.get("https://zenodo.org/api/deposit/depositions", timeout=1)


def test_the_message_says_what_to_do():
    with pytest.raises(OutboundHttpBlocked) as exc:
        requests.get("https://zenodo.org/api/deposit/depositions", timeout=1)

    message = str(exc.value)
    assert "zenodo.org" in message
    assert "permanent DOI" in message
    assert "Substitute the boundary" in message
