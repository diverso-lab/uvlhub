"""Service-level tests for the github feature.

These exercise services and repositories against a real database, without
going through the HTTP layer. Use the ``test_app`` fixture (provides an app
context + reset DB) from splent_framework.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.features.auth.repositories import UserRepository
from app.features.github.services import GithubService

pytestmark = pytest.mark.service

NEW_INFO = {"id": 12345, "login": "octocat", "name": "The Octocat"}


def _response(status_code, payload=None):
    return SimpleNamespace(status_code=status_code, json=lambda: payload, text="")


def test_get_github_user_info_returns_data_on_success(test_app):
    service = GithubService()
    with patch.object(service.github_client, "get", return_value=_response(200, {"id": 12345})):
        data, err = service.get_github_user_info(token={"access_token": "x"})

    assert err is None
    assert data["id"] == 12345


def test_get_github_user_info_reports_rate_limiting(test_app):
    service = GithubService()
    with patch.object(service.github_client, "get", return_value=_response(429)):
        data, err = service.get_github_user_info(token={"access_token": "x"})

    assert data is None
    assert "rate-limiting" in err


def test_get_github_user_info_rejects_missing_id(test_app):
    service = GithubService()
    with patch.object(service.github_client, "get", return_value=_response(200, {})):
        data, err = service.get_github_user_info(token={"access_token": "x"})

    assert data is None
    assert err


def test_get_or_create_user_creates_a_new_account(test_app, clean_database):
    user, err = GithubService().get_or_create_user(NEW_INFO)

    assert err is None
    assert user.id is not None
    assert UserRepository().count() == 1


def test_get_or_create_user_returns_existing_for_a_known_github_id(test_app, clean_database):
    service = GithubService()
    first, _ = service.get_or_create_user(NEW_INFO)
    second, err = service.get_or_create_user(NEW_INFO)

    assert err is None
    assert second.id == first.id
    assert UserRepository().count() == 1


def test_get_or_create_user_rejects_missing_information(test_app):
    user, err = GithubService().get_or_create_user(None)

    assert user is None
    assert err


def test_get_or_create_user_rejects_missing_github_id(test_app):
    user, err = GithubService().get_or_create_user({"login": "octocat"})

    assert user is None
    assert err


def test_get_or_create_user_with_empty_name_uses_login(test_app, clean_database):
    """Test that when name is empty, login is used as name."""
    user_info = {"id": 99999, "login": "mylogin", "name": ""}
    user, err = GithubService().get_or_create_user(user_info)

    assert err is None
    assert user.profile.name == "mylogin"


def test_get_or_create_user_handles_integrity_error_gracefully(test_app, clean_database):
    """Test that IntegrityError during creation returns appropriate error."""
    user_info = {"id": 55555, "login": "concurrent_user", "name": "Concurrent"}
    service = GithubService()

    with patch.object(service.repository, "create", side_effect=IntegrityError("Duplicate key", None, None)):
        user, err = service.get_or_create_user(user_info)

    assert user is None
    assert "concurrency issue" in err


def test_github_service_logs_warning_when_env_vars_missing(test_app, caplog):
    """Test that service logs warning when GitHub credentials are missing."""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.return_value = None

        service = GithubService()

        assert "GitHub login disabled" in caplog.text or service.client_id is None
