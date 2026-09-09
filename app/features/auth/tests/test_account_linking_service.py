"""Service-level tests for cross-provider account convergence.

Goal: whichever door a person uses (email / ORCID / GitHub), they must land
on the *same* ``User`` row, and the remaining providers must stay completable
or editable so they can round out the account.

The real linking logic lives in ``OrcidService.get_or_create_user`` and
``GithubService.get_or_create_user`` (not in the routes), so it is exercised
here directly against a real database, no HTTP.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.features.auth.repositories import ExternalIdentityRepository, UserRepository
from app.features.auth.services import AuthenticationService
from app.features.github.services import GithubService
from app.features.orcid.services import OrcidService
from app.features.profile.repositories import UserProfileRepository
from app.features.profile.services import UserProfileService

pytestmark = pytest.mark.service

EMAIL = "ada@example.com"
PASSWORD = "secret-123456"
ORCID_INFO = {
    "sub": "0000-0002-1111-2222",
    "given_name": "Ada",
    "family_name": "Lovelace",
    "affiliation": "Analytical Engine Co.",
}
GITHUB_INFO = {"id": 424242, "login": "adalovelace", "name": "Ada Lovelace", "email": EMAIL}


def _profile_form(**data):
    fields = {key: SimpleNamespace(data=value) for key, value in data.items()}
    return SimpleNamespace(validate=lambda: True, errors={}, **fields)


def _providers(user_id):
    return {i.provider for i in ExternalIdentityRepository().get_all_by_user(user_id)}


def _signup_with_email():
    return AuthenticationService().create_with_profile(email=EMAIL, password=PASSWORD, name="Ada", surname="Lovelace")


# --- email is the anchor -------------------------------------------------


def test_email_then_orcid_with_matching_email_converge(test_app, clean_database):
    account = _signup_with_email()

    user, err = OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)

    assert err is None
    assert user.id == account.id
    assert UserRepository().count() == 1
    assert "orcid" in _providers(user.id)


def test_email_then_github_with_matching_email_converge(test_app, clean_database):
    account = _signup_with_email()

    user, err = GithubService().get_or_create_user(GITHUB_INFO)

    assert err is None
    assert user.id == account.id
    assert UserRepository().count() == 1
    assert "github" in _providers(user.id)


def test_email_then_all_three_resolve_to_one_account(test_app, clean_database):
    account = _signup_with_email()

    orcid_user, _ = OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)
    github_user, _ = GithubService().get_or_create_user(GITHUB_INFO)

    assert orcid_user.id == account.id
    assert github_user.id == account.id
    assert UserRepository().count() == 1
    assert _providers(account.id) == {"orcid", "github"}
    # the original email credentials still belong to the same account
    assert UserRepository().get_by_email(EMAIL).check_password(PASSWORD) is True


# --- OAuth-first, then the other OAuth door -----------------------------


def test_orcid_then_github_same_email_converge(test_app, clean_database):
    orcid_user, _ = OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)

    github_user, err = GithubService().get_or_create_user(GITHUB_INFO)

    assert err is None
    assert github_user.id == orcid_user.id
    assert UserRepository().count() == 1


def test_github_then_orcid_same_email_converge(test_app, clean_database):
    github_user, _ = GithubService().get_or_create_user(GITHUB_INFO)

    orcid_user, err = OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)

    assert err is None
    assert orcid_user.id == github_user.id
    assert UserRepository().count() == 1


# --- idempotency: the same provider identity never forks the account ----


def test_second_orcid_login_returns_the_same_user(test_app, clean_database):
    first, _ = OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)
    second, err = OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)

    assert err is None
    assert second.id == first.id
    assert UserRepository().count() == 1
    orcid_ids = [i for i in ExternalIdentityRepository().get_all_by_user(first.id) if i.provider == "orcid"]
    assert len(orcid_ids) == 1


def test_second_github_login_returns_the_same_user(test_app, clean_database):
    first, _ = GithubService().get_or_create_user(GITHUB_INFO)
    second, err = GithubService().get_or_create_user(GITHUB_INFO)

    assert err is None
    assert second.id == first.id
    assert UserRepository().count() == 1


# --- no orphan accounts: every door reaches a matchable email ----------


def test_github_user_info_backfills_the_verified_primary_email(test_app):
    """GitHub profile emails are private by default; the service must fall back
    to the verified primary from /user/emails so the account can converge."""
    service = GithubService()
    responses = [
        SimpleNamespace(status_code=200, json=lambda: {"id": 555, "login": "ada", "name": "Ada"}, text=""),
        SimpleNamespace(
            status_code=200,
            json=lambda: [
                {"email": "old@example.com", "primary": False, "verified": True},
                {"email": EMAIL, "primary": True, "verified": True},
            ],
            text="",
        ),
    ]
    with patch.object(service.github_client, "get", side_effect=responses):
        data, err = service.get_github_user_info(token={"access_token": "x"})

    assert err is None
    assert data["email"] == EMAIL


def test_github_login_converges_once_the_email_is_backfilled(test_app, clean_database):
    account = _signup_with_email()

    # user_info as it looks after get_github_user_info filled in the email
    user, err = GithubService().get_or_create_user({"id": 999, "login": "ada", "name": "Ada", "email": EMAIL})

    assert err is None
    assert user.id == account.id
    assert UserRepository().count() == 1


def test_oauth_first_account_has_no_usable_password_but_stays_one_account(test_app, clean_database):
    """An account born from ORCID never set a password. Email+password login
    is impossible until a reset, but it never becomes a second account."""
    OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)

    assert UserRepository().get_by_email(EMAIL).check_password(PASSWORD) is False
    hint = AuthenticationService().get_oauth_only_login_hint(EMAIL)
    assert hint is not None and "ORCID" in hint

    again, err = OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)
    assert err is None
    assert again.email == EMAIL
    assert UserRepository().count() == 1


# --- connect flow leaves the account in login-equivalent shape ---------


def test_orcid_link_identity_writes_both_the_identity_and_the_domain_row(test_app, clean_database):
    account = _signup_with_email()

    user, err = OrcidService().link_identity(account, ORCID_INFO, email=EMAIL)

    assert err is None and user.id == account.id
    assert "orcid" in _providers(account.id)
    assert account.profile.get_orcid() == ORCID_INFO["sub"]
    # a later ORCID login now resolves this account by orcid_id, no email needed
    again, err = OrcidService().get_or_create_user(ORCID_INFO, email=None)
    assert err is None
    assert again.id == account.id
    assert UserRepository().count() == 1


def test_github_link_identity_writes_both_the_identity_and_the_domain_row(test_app, clean_database):
    account = _signup_with_email()

    user, err = GithubService().link_identity(account, GITHUB_INFO)

    assert err is None and user.id == account.id
    assert "github" in _providers(account.id)
    assert account.profile.get_github() == GITHUB_INFO["login"]
    again, err = GithubService().get_or_create_user({"id": GITHUB_INFO["id"], "login": "x", "name": "x"})
    assert err is None
    assert again.id == account.id


def test_link_identity_rejects_an_identity_owned_by_someone_else(test_app, clean_database):
    owner, _ = OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)
    other = AuthenticationService().create_with_profile(
        email="other@example.com", password=PASSWORD, name="Other", surname="Person"
    )

    user, err = OrcidService().link_identity(other, ORCID_INFO)

    assert user is None
    assert err is not None
    assert "another account" in err


# --- the other providers stay completable / editable -------------------


def test_orcid_login_fills_the_profile_from_orcid_data(test_app, clean_database):
    user, _ = OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)

    profile = user.profile
    assert profile.name == "Ada"
    assert profile.surname == "Lovelace"
    assert profile.affiliation == "Analytical Engine Co."
    assert profile.get_orcid() == ORCID_INFO["sub"]


def test_github_login_leaves_surname_blank_for_the_user_to_complete(test_app, clean_database):
    user, _ = GithubService().get_or_create_user(GITHUB_INFO)

    profile = user.profile
    assert profile.name == "Ada Lovelace"
    assert profile.surname == ""

    # the edit form lets the user finish the account
    form = _profile_form(name="Ada", surname="Lovelace", affiliation="Analytical Engine Co.")
    updated, errors = UserProfileService().update_profile(profile.id, form)
    assert errors is None
    assert updated.surname == "Lovelace"
    assert updated.affiliation == "Analytical Engine Co."


def test_linking_orcid_by_email_keeps_the_existing_profile_untouched(test_app, clean_database):
    account = _signup_with_email()
    UserProfileRepository().update(account.profile.id, affiliation="Somewhere University")

    OrcidService().get_or_create_user(ORCID_INFO, email=EMAIL)

    profile = UserRepository().get_by_id(account.id).profile
    assert profile.name == "Ada"
    assert profile.affiliation == "Somewhere University"
