from types import SimpleNamespace
from unittest.mock import patch

import pytest
import requests

from app.features.zenodo.services import ZenodoService, ZenodoUnavailableError

pytestmark = pytest.mark.unit


def _dataset(authors=None, tags=None, pub_type_value="journalarticle"):
    publication_type = SimpleNamespace(value=pub_type_value) if pub_type_value else None
    meta = SimpleNamespace(
        publication_type=publication_type,
        authors=authors or [],
        tags=tags,
        title="My title",
        description="My description",
    )
    return SimpleNamespace(ds_meta_data=meta)


def test_build_metadata_uses_anonymous_creator_when_anonymous():
    metadata = ZenodoService().build_metadata(_dataset(), anonymous=True)

    assert metadata["creators"] == [{"name": "Anonymous"}]
    assert metadata["title"] == "My title"
    assert metadata["access_right"] == "open"


def test_build_metadata_includes_real_authors():
    authors = [SimpleNamespace(name="Ada", affiliation="Analytical Engine", orcid="0000-0001")]

    metadata = ZenodoService().build_metadata(_dataset(authors=authors))

    assert metadata["creators"][0]["name"] == "Ada"
    assert metadata["creators"][0]["affiliation"] == "Analytical Engine"
    assert metadata["creators"][0]["orcid"] == "0000-0001"


def test_build_metadata_treats_none_publication_type_as_dataset():
    metadata = ZenodoService().build_metadata(_dataset(pub_type_value="none"))

    assert metadata["upload_type"] == "dataset"
    assert metadata["publication_type"] is None


def test_build_metadata_keywords_default_to_uvlhub():
    assert "uvlhub" in ZenodoService().build_metadata(_dataset())["keywords"]


def test_is_unavailable_status():
    assert ZenodoService._is_unavailable_status(503) is True
    assert ZenodoService._is_unavailable_status(404) is False


def test_extract_error_payload_falls_back_to_text():
    response = SimpleNamespace(json=lambda: (_ for _ in ()).throw(ValueError()), text="boom")

    assert ZenodoService._extract_error_payload(response) == "boom"


@patch("app.features.zenodo.services.requests.request")
def test_create_new_deposition_returns_json_on_success(mock_request):
    mock_request.return_value = SimpleNamespace(status_code=201, json=lambda: {"id": 42})

    assert ZenodoService().create_new_deposition(_dataset())["id"] == 42


@patch("app.features.zenodo.services.requests.request")
def test_create_new_deposition_raises_unavailable_on_5xx(mock_request):
    mock_request.return_value = SimpleNamespace(status_code=503, json=lambda: {}, text="down")

    with pytest.raises(ZenodoUnavailableError):
        ZenodoService().create_new_deposition(_dataset())


@patch("app.features.zenodo.services.requests.request")
def test_create_new_deposition_raises_on_client_error(mock_request):
    mock_request.return_value = SimpleNamespace(status_code=400, json=lambda: {"error": "bad"}, text="bad")

    with pytest.raises(Exception):
        ZenodoService().create_new_deposition(_dataset())


@patch("app.features.zenodo.services.requests.get")
def test_test_connection_is_true_on_200(mock_get):
    mock_get.return_value = SimpleNamespace(status_code=200)

    assert ZenodoService().test_connection() is True


@patch("app.features.zenodo.services.requests.get")
def test_test_connection_is_false_on_network_error(mock_get):
    mock_get.side_effect = requests.RequestException("boom")

    assert ZenodoService().test_connection() is False
