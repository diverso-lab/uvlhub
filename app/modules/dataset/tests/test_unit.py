from urllib.error import HTTPError
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.datastructures import MultiDict

from app import create_app
from app.modules.dataset.services import (
    DataSetService,
    DatasetMetadataUpdateError,
    DatasetMetadataValidationError,
)


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


# Test unitario que devuelve el DOI
def test_get_uvlhub_doi():
    app = create_app("testing")

    mock_dataset = MagicMock()
    mock_dataset.ds_meta_data.dataset_doi = "10.1234/test_doi"

    service = DataSetService()

    with app.app_context():
        app.config["SERVER_NAME"] = "uvlhub.io"  # ✅ aquí
        result = service.get_uvlhub_doi(mock_dataset)

    assert result == "http://uvlhub.io/doi/10.1234/test_doi"


# Test de integración para un DOI válido que devuelve un dataset
@patch("app.modules.dataset.services.DSMetaDataService.filter_by_doi")
@patch("app.modules.dataset.services.DSViewRecordService.create_cookie")
def test_subdomain_index_success(mock_create_cookie, mock_filter_by_doi, test_client):
    mock_dataset = MagicMock()
    mock_filter_by_doi.return_value = MagicMock(dataset=mock_dataset)
    mock_create_cookie.return_value = "mock_cookie"

    response = test_client.get("/doi/10.1234/datafset1/")
    # Verificamos que el dataset existe con ese DOI
    assert response.status_code == 200

    # Acceder a las cookies desde los encabezados de la respuesta
    cookies = response.headers.get("Set-Cookie")

    # Verificar que la cookie 'view_cookie' se ha establecido correctamente
    assert "view_cookie=mock_cookie" in cookies


# Test para cuando el DOI no se encuentra
def test_subdomain_index_not_found(test_client):
    response = test_client.get("/doi/10.1234/non_existent_doi/")

    # Verificar que devuelve 404 cuando no se encuentra el dataset
    assert response.status_code == 404


def _mock_dataset_for_edit():
    dataset = MagicMock()
    dataset.ds_meta_data = MagicMock()
    dataset.ds_meta_data.id = 1
    dataset.ds_meta_data.authors = []
    dataset.ds_meta_data.dataset_doi = None
    dataset.ds_meta_data.deposition_id = None
    dataset.ds_meta_data.publication_type = None
    dataset.ds_meta_data.dataset_anonymous = False
    dataset.ds_meta_data.tags = ""
    return dataset


def test_update_metadata_from_request_success():
    service = DataSetService()
    service.repository.session = MagicMock()
    service.author_repository.create = MagicMock(side_effect=lambda **kwargs: kwargs)
    service._validate_orcid = MagicMock(side_effect=["0000-0002-1825-0097", ""])
    dataset = _mock_dataset_for_edit()
    zenodo_service = MagicMock()
    zenodo_service.create_new_deposition.return_value = {"id": 101}
    zenodo_service.upload_zip = MagicMock()
    zenodo_service.publish_deposition = MagicMock()
    zenodo_service.get_doi.return_value = "10.5072/zenodo.101"

    form_data = MultiDict(
        [
            ("title", "Updated dataset"),
            ("description", "Updated description"),
            ("publication_doi", "10.9999/new-doi"),
            ("publication_type", "datamanagementplan"),
            ("dataset_type", "zenodo_anonymous"),
            ("tags[]", "tag1"),
            ("tags[]", "tag2"),
            ("authors[0][name]", "Author One"),
            ("authors[0][affiliation]", "Uni A"),
            ("authors[0][orcid]", "0000-0002-1825-0097"),
            ("authors[1][name]", "Author Two"),
            ("authors[1][affiliation]", "Uni B"),
            ("authors[1][orcid]", ""),
        ]
    )

    with patch.object(service, "zip_dataset", return_value="C:\\tmp\\dataset_1.zip"), patch(
        "app.modules.dataset.services.os.path.exists", return_value=True
    ), patch("app.modules.dataset.services.shutil.rmtree"):
        service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    assert dataset.ds_meta_data.title == "Updated dataset"
    assert dataset.ds_meta_data.description == "Updated description"
    assert dataset.ds_meta_data.publication_doi == "10.9999/new-doi"
    assert dataset.ds_meta_data.tags == "tag1,tag2"
    assert dataset.ds_meta_data.dataset_anonymous is True
    assert dataset.ds_meta_data.publication_type.value == "datamanagementplan"
    assert len(dataset.ds_meta_data.authors) == 2
    assert dataset.ds_meta_data.deposition_id == 101
    assert dataset.ds_meta_data.dataset_doi == "10.5072/zenodo.101"
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_duplicate_orcid_raises_validation_error():
    service = DataSetService()
    service.repository.session = MagicMock()
    service.author_repository.create = MagicMock(side_effect=lambda **kwargs: kwargs)
    service._validate_orcid = MagicMock(return_value="0000-0002-1825-0097")
    dataset = _mock_dataset_for_edit()

    form_data = MultiDict(
        [
            ("title", "Updated dataset"),
            ("description", "Updated description"),
            ("authors[0][name]", "Author One"),
            ("authors[0][affiliation]", "Uni A"),
            ("authors[0][orcid]", "0000-0002-1825-0097"),
            ("authors[1][name]", "Author Two"),
            ("authors[1][affiliation]", "Uni B"),
            ("authors[1][orcid]", "0000-0002-1825-0097"),
        ]
    )

    with pytest.raises(DatasetMetadataValidationError, match="Duplicate author detected: ORCID"):
        service.update_metadata_from_request(dataset, form_data)

    service.repository.session.rollback.assert_called_once()


def test_validate_orcid_invalid_checksum():
    service = DataSetService()
    with patch("app.modules.dataset.services.urllib_request.urlopen") as mock_urlopen:
        with pytest.raises(DatasetMetadataValidationError, match="Invalid ORCID checksum"):
            service._validate_orcid("0000-0002-1825-0096")
        mock_urlopen.assert_not_called()


def test_validate_orcid_not_found():
    service = DataSetService()
    with patch(
        "app.modules.dataset.services.urllib_request.urlopen",
        side_effect=HTTPError(url="", code=404, msg="Not Found", hdrs=None, fp=None),
    ):
        with pytest.raises(DatasetMetadataValidationError, match="ORCID not found"):
            service._validate_orcid("0000-0002-1825-0097")


def test_update_metadata_from_request_wraps_unexpected_errors():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    form_data = MultiDict([("title", "Updated dataset"), ("description", "Updated description")])

    with patch.object(service, "_replace_authors_from_form", side_effect=RuntimeError("boom")):
        with pytest.raises(DatasetMetadataUpdateError, match="boom"):
            service.update_metadata_from_request(dataset, form_data)

    service.repository.session.rollback.assert_called_once()


def test_update_metadata_from_request_duplicate_name_affiliation_without_orcid_raises_validation_error():
    service = DataSetService()
    service.repository.session = MagicMock()
    service.author_repository.create = MagicMock(side_effect=lambda **kwargs: kwargs)
    service._validate_orcid = MagicMock(return_value="")
    dataset = _mock_dataset_for_edit()

    form_data = MultiDict(
        [
            ("title", "Updated dataset"),
            ("description", "Updated description"),
            ("authors[0][name]", "Same Author"),
            ("authors[0][affiliation]", "Same Uni"),
            ("authors[0][orcid]", ""),
            ("authors[1][name]", "Same Author"),
            ("authors[1][affiliation]", "Same Uni"),
            ("authors[1][orcid]", ""),
        ]
    )

    with pytest.raises(DatasetMetadataValidationError, match="Duplicate author detected: same name and affiliation"):
        service.update_metadata_from_request(dataset, form_data)

    service.repository.session.rollback.assert_called_once()


def test_validate_orcid_invalid_format():
    service = DataSetService()
    with pytest.raises(DatasetMetadataValidationError, match="Invalid ORCID format"):
        service._validate_orcid("12345")


def test_update_metadata_from_request_invalid_publication_type_falls_back_to_other():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()

    form_data = MultiDict(
        [
            ("title", "Updated dataset"),
            ("description", "Updated description"),
            ("publication_type", "not_a_valid_type"),
        ]
    )

    service.update_metadata_from_request(dataset, form_data)

    assert dataset.ds_meta_data.publication_type.name == "OTHER"
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_parses_tags_from_csv_when_tags_array_missing():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()

    form_data = MultiDict(
        [
            ("title", "Updated dataset"),
            ("description", "Updated description"),
            ("tags", "tag1, tag2 ,tag3"),
        ]
    )

    service.update_metadata_from_request(dataset, form_data)

    assert dataset.ds_meta_data.tags == "tag1,tag2,tag3"
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_empty_orcid_is_allowed():
    service = DataSetService()
    service.repository.session = MagicMock()
    service.author_repository.create = MagicMock(side_effect=lambda **kwargs: kwargs)
    service._validate_orcid = MagicMock(return_value="")
    dataset = _mock_dataset_for_edit()

    form_data = MultiDict(
        [
            ("title", "Updated dataset"),
            ("description", "Updated description"),
            ("authors[0][name]", "Author One"),
            ("authors[0][affiliation]", "Uni A"),
            ("authors[0][orcid]", ""),
        ]
    )

    service.update_metadata_from_request(dataset, form_data)

    assert len(dataset.ds_meta_data.authors) == 1
    assert dataset.ds_meta_data.authors[0]["orcid"] == ""
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_draft_sets_dataset_anonymous_false():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()

    form_data = MultiDict(
        [
            ("title", "Updated dataset"),
            ("description", "Updated description"),
            ("dataset_type", "draft"),
        ]
    )

    service.update_metadata_from_request(dataset, form_data)

    assert dataset.ds_meta_data.dataset_anonymous is False
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_synced_dataset_updates_zenodo_deposition():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = "10.1234/demo"
    dataset.ds_meta_data.deposition_id = 99

    zenodo_service = MagicMock()
    zenodo_service.build_metadata.return_value = {"title": "Updated dataset"}
    zenodo_service.update_deposition = MagicMock()

    form_data = MultiDict(
        [("title", "Updated dataset"), ("description", "Updated description"), ("dataset_type", "zenodo")]
    )

    service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    zenodo_service.build_metadata.assert_called_once()
    zenodo_service.update_deposition.assert_called_once_with(99, {"title": "Updated dataset"})
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_synced_dataset_without_deposition_id_raises_error():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = "10.1234/demo"
    dataset.ds_meta_data.deposition_id = None

    zenodo_service = MagicMock()
    form_data = MultiDict(
        [("title", "Updated dataset"), ("description", "Updated description"), ("dataset_type", "zenodo")]
    )

    with pytest.raises(DatasetMetadataUpdateError, match="missing Zenodo deposition_id"):
        service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    service.repository.session.rollback.assert_called_once()


def test_update_metadata_from_request_synced_dataset_to_draft_clears_zenodo_fields():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = "10.1234/demo"
    dataset.ds_meta_data.deposition_id = 99

    zenodo_service = MagicMock()
    form_data = MultiDict(
        [("title", "Updated dataset"), ("description", "Updated description"), ("dataset_type", "draft")]
    )

    service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    assert dataset.ds_meta_data.dataset_doi is None
    assert dataset.ds_meta_data.deposition_id is None
    zenodo_service.update_deposition.assert_not_called()
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_unsynced_dataset_to_zenodo_publishes_and_sets_doi():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = None
    dataset.ds_meta_data.deposition_id = None

    zenodo_service = MagicMock()
    zenodo_service.create_new_deposition.return_value = {"id": 101}
    zenodo_service.upload_zip = MagicMock()
    zenodo_service.publish_deposition = MagicMock()
    zenodo_service.get_doi.return_value = "10.5072/zenodo.101"

    with patch.object(service, "zip_dataset", return_value="C:\\tmp\\dataset_1.zip"), patch(
        "app.modules.dataset.services.os.path.exists", return_value=True
    ), patch("app.modules.dataset.services.shutil.rmtree"):
        form_data = MultiDict(
            [("title", "Updated dataset"), ("description", "Updated description"), ("dataset_type", "zenodo")]
        )
        service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    zenodo_service.create_new_deposition.assert_called_once()
    zenodo_service.upload_zip.assert_called_once_with(dataset, 101, "C:\\tmp\\dataset_1.zip")
    zenodo_service.publish_deposition.assert_called_once_with(101)
    assert dataset.ds_meta_data.deposition_id == 101
    assert dataset.ds_meta_data.dataset_doi == "10.5072/zenodo.101"
    service.repository.session.commit.assert_called_once()
