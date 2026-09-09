"""HTTP integration tests for cross-provider account convergence.

Drive the whole flow through the Flask test client with the OAuth boundary
mocked (``conftest`` blocks real outbound HTTP on purpose). Each provider
callback is exercised end to end: ``/orcid/authorize`` and
``/github/authorize`` build their service through ``before_app_request``, so
patching ``configure_oauth`` on the class is enough to inject a fake client.
"""

from unittest.mock import MagicMock, patch

import pytest
from flask import current_app, redirect

from app.features.auth.repositories import ExternalIdentityRepository, UserRepository
from app.features.github.services import GithubService
from app.features.orcid.services import OrcidService

pytestmark = pytest.mark.integration

EMAIL = "grace@example.com"
PASSWORD = "secret-123456"
ORCID_INFO = {"sub": "0000-0003-4444-5555", "given_name": "Grace", "family_name": "Hopper"}
GITHUB_INFO = {"id": 707070, "login": "gracehopper", "name": "Grace Hopper", "email": EMAIL}


def _drop_oauth_services():
    """Drop the cached provider services so the next request rebuilds them
    through the currently-active ``configure_oauth`` patch."""
    app = current_app._get_current_object()
    for attr in ("orcid_service", "github_service"):
        if hasattr(app, attr):
            delattr(app, attr)


@pytest.fixture(autouse=True)
def _clean_slate(test_client, clean_database):
    """Every test starts with an empty database and a logged-out client, and
    with the cached OAuth services dropped so patches take effect."""
    _drop_oauth_services()
    test_client.get("/logout", follow_redirects=False)
    yield
    test_client.get("/logout", follow_redirects=False)
    _drop_oauth_services()


def _mock_oauth_client(provider_url):
    client = MagicMock()
    client.authorize_redirect.return_value = redirect(provider_url)
    client.authorize_access_token.return_value = {"access_token": "token123"}
    return (MagicMock(), client)


def _signup_with_email(test_client):
    with patch("app.features.auth.routes.captcha_service.validate_captcha", return_value=True):
        test_client.post(
            "/signup/",
            data=dict(
                name="Grace",
                surname="Hopper",
                email=EMAIL,
                password=PASSWORD,
                confirm_password=PASSWORD,
                captcha="x",
            ),
            follow_redirects=True,
        )
    test_client.get("/logout", follow_redirects=True)


def _orcid_authorize(test_client, user_info, *, session_updates=None):
    with test_client.session_transaction() as sess:
        for key, value in (session_updates or {}).items():
            sess[key] = value
    with (
        patch.object(
            OrcidService, "configure_oauth", return_value=_mock_oauth_client("https://orcid.org/oauth/authorize")
        ),
        patch.object(OrcidService, "get_orcid_user_info", return_value=(user_info, None)),
    ):
        _drop_oauth_services()
        return test_client.get("/orcid/authorize?code=x&state=y", follow_redirects=False)


def _github_authorize(test_client, user_info, *, session_updates=None):
    with test_client.session_transaction() as sess:
        for key, value in (session_updates or {}).items():
            sess[key] = value
    with (
        patch.object(
            GithubService,
            "configure_oauth",
            return_value=_mock_oauth_client("https://github.com/login/oauth/authorize"),
        ),
        patch.object(GithubService, "get_github_user_info", return_value=(user_info, None)),
    ):
        _drop_oauth_services()
        return test_client.get("/github/authorize?code=x&state=y", follow_redirects=False)


# --- login entry points wire the providers together --------------------


def test_login_page_offers_all_three_doors(test_client):
    test_client.get("/logout", follow_redirects=True)
    response = test_client.get("/login")

    assert response.status_code == 200
    assert b"/github/login" in response.data
    assert b"/orcid/login-email" in response.data


def test_orcid_login_email_stores_the_email_in_session(test_client, clean_database):
    response = test_client.post("/orcid/login-email", data={"email": EMAIL}, follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/orcid/login")
    with test_client.session_transaction() as sess:
        assert sess["orcid_login_email"] == EMAIL


# --- convergence over HTTP --------------------------------------------


def test_email_signup_then_orcid_callback_converge(test_client, clean_database):
    _signup_with_email(test_client)
    assert UserRepository().count() == 1
    account_id = UserRepository().get_by_email(EMAIL).id

    response = _orcid_authorize(test_client, ORCID_INFO, session_updates={"orcid_login_email": EMAIL})

    assert response.status_code == 302
    assert UserRepository().count() == 1
    identities = ExternalIdentityRepository().get_all_by_user(account_id)
    assert {i.provider for i in identities} == {"orcid"}


def test_email_signup_then_github_callback_converge(test_client, clean_database):
    _signup_with_email(test_client)
    account_id = UserRepository().get_by_email(EMAIL).id

    response = _github_authorize(test_client, GITHUB_INFO)

    assert response.status_code == 302
    assert UserRepository().count() == 1
    identities = ExternalIdentityRepository().get_all_by_user(account_id)
    assert {i.provider for i in identities} == {"github"}


def test_orcid_callback_then_github_callback_converge(test_client, clean_database):
    _orcid_authorize(test_client, ORCID_INFO, session_updates={"orcid_login_email": EMAIL})
    test_client.get("/logout", follow_redirects=True)
    account_id = UserRepository().get_by_email(EMAIL).id

    _github_authorize(test_client, GITHUB_INFO)

    assert UserRepository().count() == 1
    identities = ExternalIdentityRepository().get_all_by_user(account_id)
    assert {i.provider for i in identities} == {"orcid", "github"}


def test_repeated_orcid_callback_does_not_fork_the_account(test_client, clean_database):
    _orcid_authorize(test_client, ORCID_INFO, session_updates={"orcid_login_email": EMAIL})
    test_client.get("/logout", follow_redirects=True)
    _orcid_authorize(test_client, ORCID_INFO, session_updates={"orcid_login_email": EMAIL})

    assert UserRepository().count() == 1


# --- no door lets you skip the email that ties accounts together -------


def test_orcid_login_without_an_email_redirects_to_the_email_step(test_client, clean_database):
    response = test_client.get("/orcid/login", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/orcid/login-email")


def test_orcid_callback_without_an_email_bounces_back_instead_of_creating_an_account(test_client, clean_database):
    # reach /orcid/authorize with no email in session and an unknown ORCID iD
    response = _orcid_authorize(test_client, ORCID_INFO)

    assert response.status_code == 302
    assert "/orcid/login-email" in response.location
    assert UserRepository().count() == 0


def test_orcid_callback_uses_the_email_from_the_orcid_claim_when_present(test_client, clean_database):
    _signup_with_email(test_client)
    account_id = UserRepository().get_by_email(EMAIL).id

    # no typed email, but ORCID's userinfo carries it -> still converges
    response = _orcid_authorize(test_client, {**ORCID_INFO, "email": EMAIL})

    assert response.status_code == 302
    assert UserRepository().count() == 1
    assert {i.provider for i in ExternalIdentityRepository().get_all_by_user(account_id)} == {"orcid"}


def test_github_callback_links_by_the_backfilled_private_email(test_client, clean_database):
    _signup_with_email(test_client)
    account_id = UserRepository().get_by_email(EMAIL).id

    # get_github_user_info returns the email it recovered from /user/emails
    response = _github_authorize(test_client, {"id": 909090, "login": "grace", "name": "Grace", "email": EMAIL})

    assert response.status_code == 302
    assert UserRepository().count() == 1
    assert {i.provider for i in ExternalIdentityRepository().get_all_by_user(account_id)} == {"github"}


def test_github_callback_without_any_email_does_not_create_an_orphan_account(test_client, clean_database):
    response = _github_authorize(test_client, {"id": 121212, "login": "noemail", "name": "No Email"})

    assert response.status_code == 302
    assert "/login" in response.location
    assert UserRepository().count() == 0


# --- connect flow: rounding out an already-authenticated account -------


def test_connect_orcid_while_logged_in_with_email(test_client, clean_database):
    _signup_with_email(test_client)
    test_client.post("/login", data={"email": EMAIL, "password": PASSWORD}, follow_redirects=True)
    account_id = UserRepository().get_by_email(EMAIL).id

    redirect_resp = test_client.get("/account/connect/orcid", follow_redirects=False)
    assert redirect_resp.status_code == 302
    with test_client.session_transaction() as sess:
        assert sess.get("orcid_connect_mode") is True

    response = _orcid_authorize(test_client, ORCID_INFO)

    assert response.status_code == 302
    assert response.location.endswith("/profile/edit")
    assert UserRepository().count() == 1
    identities = ExternalIdentityRepository().get_all_by_user(account_id)
    assert {i.provider for i in identities} == {"orcid"}
    # the connect flow now also writes the Orcid domain row
    assert UserRepository().get_by_email(EMAIL).profile.get_orcid() == ORCID_INFO["sub"]


def test_connect_github_while_logged_in_with_email(test_client, clean_database):
    _signup_with_email(test_client)
    test_client.post("/login", data={"email": EMAIL, "password": PASSWORD}, follow_redirects=True)
    account_id = UserRepository().get_by_email(EMAIL).id

    test_client.get("/account/connect/github", follow_redirects=False)
    response = _github_authorize(test_client, GITHUB_INFO)

    assert response.status_code == 302
    assert response.location.endswith("/profile/edit")
    identities = ExternalIdentityRepository().get_all_by_user(account_id)
    assert {i.provider for i in identities} == {"github"}
    assert UserRepository().get_by_email(EMAIL).profile.get_github() == GITHUB_INFO["login"]


# --- the remaining fields stay editable to verify the account ----------


def test_profile_edit_after_github_login_shows_editable_fields_and_the_other_providers(test_client, clean_database):
    _github_authorize(test_client, GITHUB_INFO)  # logs the new user in

    response = test_client.get("/profile/edit")

    assert response.status_code == 200
    body = response.data.decode()
    # name pre-filled from GitHub, surname left blank for the user to complete
    assert 'name="name"' in body and "Grace Hopper" in body
    assert 'name="surname"' in body
    assert 'name="affiliation"' in body
    # ORCID is not linked yet, so the connect entry point is offered
    assert "/account/connect/orcid" in body
    assert "/account/connect/github" not in body
