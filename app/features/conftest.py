import http.client
import urllib.request

import pytest
import requests.adapters

from app import create_app, db
from app.features.auth.models import User
from app.features.profile.models import UserProfile


class OutboundHttpBlocked(RuntimeError):
    """A test tried to reach a real service over HTTP."""


_BLOCKED_MESSAGE = (
    "This test tried to open an outbound HTTP connection to {target}.\n"
    "Publishing to Zenodo mints a permanent DOI that nobody can delete, and a "
    "test run has already done that by accident, so the transport is closed for "
    "the whole suite rather than trusting each test to mock it.\n"
    "Substitute the boundary in your test, for example the zenodo_service or the "
    "function under test, instead of letting the request through. Browser tests "
    "need the selenium grid and are exempt through the e2e marker."
)


def _blocked(target):
    raise OutboundHttpBlocked(_BLOCKED_MESSAGE.format(target=target))


@pytest.fixture(autouse=True)
def block_outbound_http(request):
    """Close the HTTP transport for every test that is not browser driven.

    Mocking at the call site is what the suite relied on before, and it failed
    the moment one test undid a shared patch: the run reached production Zenodo
    and minted three permanent DOIs. A guard one layer below the library cannot
    be undone by accident, because nothing in the application talks to Zenodo
    without going through one of these three doors.

    It owns a PRIVATE MonkeyPatch on purpose. Taking the shared monkeypatch
    fixture would put these patches on the same undo stack as the test's own,
    which is precisely how the accident happened: one undo() reopened the
    transport for everything that ran afterwards.

    The database is untouched: it speaks its own protocol on a raw socket, not
    HTTP, so blocking here never hides an infrastructure problem.
    """
    if request.node.get_closest_marker("e2e") or request.node.get_closest_marker("load"):
        yield
        return

    def send(self, req, *args, **kwargs):
        _blocked(getattr(req, "url", "an unknown URL"))

    def urlopen(url, *args, **kwargs):
        _blocked(getattr(url, "full_url", url))

    def http_request(self, method, url, *args, **kwargs):
        _blocked(f"{self.host}{url}")

    with pytest.MonkeyPatch().context() as guard:
        guard.setattr(requests.adapters.HTTPAdapter, "send", send)
        guard.setattr(urllib.request, "urlopen", urlopen)
        guard.setattr(http.client.HTTPConnection, "request", http_request)
        yield


@pytest.fixture(scope="session")
def test_app():
    """Create and configure a new app instance for each test session."""
    test_app = create_app("testing")

    with test_app.app_context():
        yield test_app


@pytest.fixture(scope="module")
def test_client(test_app):

    with test_app.test_client() as testing_client:
        with test_app.app_context():

            db.drop_all()
            db.create_all()
            """
            The test suite always includes the following user in order to avoid repetition
            of its creation
            """
            user_test = User(email="test@example.com", password="test1234")
            db.session.add(user_test)
            db.session.commit()

            profile = UserProfile(user_id=user_test.id, name="Test", surname="User")
            db.session.add(profile)
            db.session.commit()

            yield testing_client

            db.session.remove()
            db.drop_all()


@pytest.fixture(scope="function")
def clean_database():
    db.session.remove()
    db.drop_all()
    db.create_all()
    yield
    db.session.remove()
    db.drop_all()
    db.create_all()


def login(test_client, email, password):
    """
    Authenticates the user with the credentials provided.

    Args:
        test_client: Flask test client.
        email (str): User's email address.
        password (str): User's password.

    Returns:
        response: POST login request response.
    """
    response = test_client.post("/login", data=dict(email=email, password=password), follow_redirects=True)
    return response


def logout(test_client):
    """
    Logs out the user.

    Args:
        test_client: Flask test client.

    Returns:
        response: Response to GET request to log out.
    """
    return test_client.get("/logout", follow_redirects=True)
