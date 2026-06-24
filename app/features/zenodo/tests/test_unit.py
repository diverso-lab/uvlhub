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


def _response(status_code, payload=None, text="", reason=""):
    return SimpleNamespace(status_code=status_code, json=lambda: payload, text=text, reason=reason)


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


@patch("app.features.zenodo.services.requests.get")
def test_get_all_depositions_returns_json(mock_get):
    mock_get.return_value = _response(200, [{"id": 1}])

    assert ZenodoService().get_all_depositions() == [{"id": 1}]


@patch("app.features.zenodo.services.requests.get")
def test_get_all_depositions_raises_on_failure(mock_get):
    mock_get.return_value = _response(500)

    with pytest.raises(Exception):
        ZenodoService().get_all_depositions()


@patch("app.features.zenodo.services.requests.request")
def test_upload_zip_returns_json_on_success(mock_request, tmp_path):
    zip_path = tmp_path / "dataset.zip"
    zip_path.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    mock_request.return_value = _response(201, {"id": 9})

    assert ZenodoService().upload_zip(_dataset(), 9, str(zip_path))["id"] == 9


@patch("app.features.zenodo.services.requests.request")
def test_upload_zip_raises_unavailable_on_5xx(mock_request, tmp_path):
    zip_path = tmp_path / "dataset.zip"
    zip_path.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    mock_request.return_value = _response(
        503,
        None,
    )

    with pytest.raises(ZenodoUnavailableError):
        ZenodoService().upload_zip(_dataset(), 9, str(zip_path))


@patch("app.features.zenodo.services.requests.request")
def test_publish_deposition_succeeds_on_202(mock_request):
    mock_request.return_value = _response(202)

    ZenodoService().publish_deposition(9)  # must not raise


@patch("app.features.zenodo.services.requests.request")
def test_publish_deposition_raises_on_error(mock_request):
    mock_request.return_value = _response(400, {"error": "bad"})

    with pytest.raises(Exception):
        ZenodoService().publish_deposition(9)


@patch("app.features.zenodo.services.requests.request")
def test_get_deposition_and_get_doi(mock_request):
    mock_request.return_value = _response(200, {"id": 9, "doi": "10.5072/zenodo.9"})
    service = ZenodoService()

    assert service.get_deposition(9)["id"] == 9
    assert service.get_doi(9) == "10.5072/zenodo.9"


@patch("app.features.zenodo.services.requests.request")
def test_update_deposition_edits_updates_and_publishes(mock_request):
    # edit (201) -> update (200) -> publish (202)
    mock_request.side_effect = [_response(201), _response(200, {"id": 9}), _response(202)]

    result = ZenodoService().update_deposition(9, {"title": "t"})

    assert result == {"id": 9}
    assert mock_request.call_count == 3


def test_build_metadata_includes_version_when_provided():
    metadata = ZenodoService().build_metadata(_dataset(), version="3")

    assert metadata["version"] == "3"


@patch("app.features.zenodo.services.requests.request")
def test_create_new_version_draft_returns_new_deposition_id(mock_request):
    mock_request.return_value = _response(
        201, {"links": {"latest_draft": "https://sandbox.zenodo.org/api/deposit/depositions/777"}}
    )

    assert ZenodoService().create_new_version_draft(111) == 777


@patch("app.features.zenodo.services.requests.request")
def test_create_new_version_draft_raises_without_latest_draft(mock_request):
    mock_request.return_value = _response(201, {"links": {}})

    with pytest.raises(Exception, match="latest_draft"):
        ZenodoService().create_new_version_draft(111)


@patch("app.features.zenodo.services.requests.request")
def test_delete_all_deposition_files_deletes_every_file(mock_request):
    mock_request.side_effect = [_response(200, [{"id": "a"}, {"id": "b"}]), _response(204), _response(204)]

    ZenodoService().delete_all_deposition_files(5)

    assert mock_request.call_count == 3


@patch("app.features.zenodo.services.requests.request")
def test_update_draft_metadata_raises_on_error(mock_request):
    mock_request.return_value = _response(400, {"error": "bad"})

    with pytest.raises(Exception):
        ZenodoService().update_draft_metadata(5, {"title": "x"})
