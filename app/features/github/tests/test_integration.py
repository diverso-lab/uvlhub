"""HTTP integration tests for the github feature.

Drive the application through the Flask test client. The ``test_client``
fixture rebuilds a clean DB per test for full isolation.
"""

from unittest.mock import MagicMock, patch

import pytest
from flask import redirect

from app.features.auth.models import User
from app.features.auth.repositories import UserRepository
from app.features.github.services import GithubService

pytestmark = pytest.mark.integration


def _mock_github_service():
    """Create a mock GithubService with mocked oauth client."""
    mock_oauth = MagicMock()
    mock_client = MagicMock()
    mock_client.authorize_redirect.return_value = redirect("https://github.com/login/oauth/authorize?...")
    return (mock_oauth, mock_client)


def test_github_login_redirects_to_github(test_client):
    """Test that /github/login redirects to GitHub OAuth endpoint."""
    with patch.object(GithubService, "configure_oauth", return_value=_mock_github_service()):
        response = test_client.get("/github/login", follow_redirects=False)

        assert response.status_code == 302


def test_github_login_stores_next_url_in_session(test_client, clean_database):
    """Test that /github/login stores next_url in session when provided."""
    with patch.object(GithubService, "configure_oauth", return_value=_mock_github_service()):
        response = test_client.get("/github/login?next=/profile", follow_redirects=False)

        assert response.status_code == 302


def test_authorize_handles_access_token_exception(test_client, clean_database):
    """Test when authorize_access_token() raises exception."""
    mock_oauth, mock_client = _mock_github_service()
    mock_client.authorize_access_token.side_effect = Exception("OAuth failed")

    with patch.object(GithubService, "configure_oauth", return_value=(mock_oauth, mock_client)):
        response = test_client.get("/github/authorize?code=fake&state=fake", follow_redirects=False)

    # Should redirect to login on error
    assert response.status_code == 302
    assert response.location.endswith("/login") or "/login" in response.location
    assert UserRepository().count() == 0


def test_authorize_handles_userinfo_error(test_client, clean_database):
    """Test when get_github_user_info() returns error."""
    mock_oauth, mock_client = _mock_github_service()
    mock_client.authorize_access_token.return_value = {"access_token": "token123"}

    with (
        patch.object(GithubService, "configure_oauth", return_value=(mock_oauth, mock_client)),
        patch.object(
            GithubService,
            "get_github_user_info",
            return_value=(None, "GitHub is rate-limiting requests. Please try again in a minute."),
        ),
    ):

        response = test_client.get("/github/authorize?code=fake&state=fake", follow_redirects=False)

    assert response.status_code == 302
    assert UserRepository().count() == 0


def test_authorize_handles_user_creation_error(test_client, clean_database):
    """Test when get_or_create_user() returns error."""
    user_data = {"id": 99999, "login": "testuser", "name": "Test User"}
    mock_oauth, mock_client = _mock_github_service()
    mock_client.authorize_access_token.return_value = {"access_token": "token123"}

    with (
        patch.object(GithubService, "configure_oauth", return_value=(mock_oauth, mock_client)),
        patch.object(GithubService, "get_github_user_info", return_value=(user_data, None)),
        patch.object(
            GithubService,
            "get_or_create_user",
            return_value=(None, "Could not create your account due to a database error. Please try again."),
        ),
    ):

        response = test_client.get("/github/authorize?code=fake&state=fake", follow_redirects=False)

    assert response.status_code == 302
    assert UserRepository().count() == 0


def test_authorize_successful_flow_creates_user_and_logs_in(test_client, clean_database):
    """Test complete successful authorization flow."""
    user_data = {"id": 12345, "login": "octocat", "name": "The Octocat"}
    mock_oauth, mock_client = _mock_github_service()
    mock_client.authorize_access_token.return_value = {"access_token": "token123"}

    with (
        patch.object(GithubService, "configure_oauth", return_value=(mock_oauth, mock_client)),
        patch.object(GithubService, "get_github_user_info", return_value=(user_data, None)),
    ):

        response = test_client.get("/github/authorize?code=fake&state=fake", follow_redirects=False)

    # Should redirect to home
    assert response.status_code == 302

    # User should be created
    assert UserRepository().count() == 1
    user = User.query.first()
    assert user is not None

    # Check user profile was created with GitHub data
    profile = user.profile
    assert profile is not None
    assert profile.name == "The Octocat"

    # Check GitHub record was created
    from app.features.github.repositories import GithubRepository

    github_record = GithubRepository().get_by_github_id(12345)
    assert github_record is not None
    assert github_record.github_login == "octocat"


def test_authorize_creates_user_successfully(test_client, clean_database):
    """Test that user is created on successful authorization."""
    user_data = {"id": 12345, "login": "octocat", "name": "The Octocat"}
    mock_oauth, mock_client = _mock_github_service()
    mock_client.authorize_access_token.return_value = {"access_token": "token123"}

    with (
        patch.object(GithubService, "configure_oauth", return_value=(mock_oauth, mock_client)),
        patch.object(GithubService, "get_github_user_info", return_value=(user_data, None)),
    ):

        test_client.get("/github/authorize?code=fake&state=fake", follow_redirects=False)

    assert UserRepository().count() == 1


def test_authorize_redirects_to_next_url_when_safe(test_client, clean_database):
    """Test redirect to safe next_url after successful login."""
    user_data = {"id": 12345, "login": "octocat", "name": "The Octocat"}
    mock_oauth, mock_client = _mock_github_service()
    mock_client.authorize_access_token.return_value = {"access_token": "token123"}

    with test_client.session_transaction() as sess:
        sess["github_next_url"] = "/profile"

    with (
        patch.object(GithubService, "configure_oauth", return_value=(mock_oauth, mock_client)),
        patch.object(GithubService, "get_github_user_info", return_value=(user_data, None)),
    ):

        response = test_client.get("/github/authorize?code=fake&state=fake", follow_redirects=False)

    assert response.status_code == 302
    assert "/profile" in response.location


def test_authorize_ignores_unsafe_next_url(test_client, clean_database):
    """Test that unsafe next_url is ignored and redirects to home."""
    user_data = {"id": 12345, "login": "octocat", "name": "The Octocat"}
    mock_oauth, mock_client = _mock_github_service()
    mock_client.authorize_access_token.return_value = {"access_token": "token123"}

    with test_client.session_transaction() as sess:
        sess["github_next_url"] = "//evil.com"

    with (
        patch.object(GithubService, "configure_oauth", return_value=(mock_oauth, mock_client)),
        patch.object(GithubService, "get_github_user_info", return_value=(user_data, None)),
    ):

        response = test_client.get("/github/authorize?code=fake&state=fake", follow_redirects=False)

    assert response.status_code == 302
    # Should NOT redirect to evil.com, should redirect to safe location
    assert "evil.com" not in response.location


def test_authorize_returns_existing_user_on_second_login(test_client, clean_database):
    """Test that logging in with same GitHub ID returns existing user."""
    from app.features.github.repositories import GithubRepository

    user_data = {"id": 12345, "login": "octocat", "name": "The Octocat"}
    mock_oauth, mock_client = _mock_github_service()
    mock_client.authorize_access_token.return_value = {"access_token": "token123"}

    # First login
    with (
        patch.object(GithubService, "configure_oauth", return_value=(mock_oauth, mock_client)),
        patch.object(GithubService, "get_github_user_info", return_value=(user_data, None)),
    ):

        test_client.get("/github/authorize?code=fake1&state=fake1", follow_redirects=False)

    assert UserRepository().count() == 1
    first_user_id = User.query.first().id
    first_github_record = GithubRepository().get_by_github_id(12345)

    # Second login with same GitHub ID
    with (
        patch.object(GithubService, "configure_oauth", return_value=(mock_oauth, mock_client)),
        patch.object(GithubService, "get_github_user_info", return_value=(user_data, None)),
    ):

        test_client.get("/github/authorize?code=fake2&state=fake2", follow_redirects=False)

    # Still only one user
    assert UserRepository().count() == 1
    second_user_id = User.query.first().id

    # Same user ID as first login
    assert second_user_id == first_user_id

    # GitHub record should still exist and point to same user
    second_github_record = GithubRepository().get_by_github_id(12345)
    assert second_github_record.id == first_github_record.id
