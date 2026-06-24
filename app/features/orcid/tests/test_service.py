from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.features.auth.repositories import UserRepository
from app.features.orcid.services import OrcidService

pytestmark = pytest.mark.service

NEW_INFO = {"sub": "0000-0001-2345-6789", "given_name": "Ada", "family_name": "Lovelace"}


def _response(status_code, payload=None):
    return SimpleNamespace(status_code=status_code, json=lambda: payload, text="")


def test_get_orcid_user_info_returns_data_on_success(test_app):
    service = OrcidService()
    with patch.object(service.orcid_client, "get", return_value=_response(200, {"sub": "0000-0001"})):
        data, err = service.get_orcid_user_info(token={"access_token": "x"})

    assert err is None
    assert data["sub"] == "0000-0001"


def test_get_orcid_user_info_reports_rate_limiting(test_app):
    service = OrcidService()
    with patch.object(service.orcid_client, "get", return_value=_response(429)):
        data, err = service.get_orcid_user_info(token={"access_token": "x"})

    assert data is None
    assert "rate-limiting" in err


def test_get_orcid_user_info_rejects_missing_sub(test_app):
    service = OrcidService()
    with patch.object(service.orcid_client, "get", return_value=_response(200, {})):
        data, err = service.get_orcid_user_info(token={"access_token": "x"})

    assert data is None
    assert err


def test_get_or_create_user_creates_a_new_account(test_app, clean_database):
    user, err = OrcidService().get_or_create_user(NEW_INFO)

    assert err is None
    assert user.id is not None
    assert UserRepository().count() == 1


def test_get_or_create_user_returns_existing_for_a_known_orcid(test_app, clean_database):
    service = OrcidService()
    first, _ = service.get_or_create_user(NEW_INFO)
    second, err = service.get_or_create_user(NEW_INFO)

    assert err is None
    assert second.id == first.id
    assert UserRepository().count() == 1


def test_get_or_create_user_rejects_missing_information(test_app):
    user, err = OrcidService().get_or_create_user(None)

    assert user is None
    assert err


def test_get_or_create_user_rejects_missing_orcid_id(test_app):
    user, err = OrcidService().get_or_create_user({"given_name": "Ada"})

    assert user is None
    assert err
