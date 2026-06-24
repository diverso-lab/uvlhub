from unittest.mock import MagicMock, patch

import pytest
from werkzeug.datastructures import MultiDict

from app import create_app
from app.features.dataset.services import (
    DatasetMetadataUpdateError,
    DatasetMetadataValidationError,
    DataSetService,
)
from app.features.zenodo.services import ZenodoUnavailableError

pytestmark = pytest.mark.service


def _mock_dataset_for_edit():
    dataset = MagicMock()
    dataset.ds_meta_data = MagicMock()
    dataset.ds_meta_data.id = 1
    dataset.ds_meta_data.authors = []
    dataset.ds_meta_data.dataset_doi = None
    dataset.ds_meta_data.deposition_id = None
    dataset.ds_meta_data.publication_type = None
    dataset.ds_meta_data.dataset_anonymous = False
    dataset.ds_meta_data.metadata_synced = True
    dataset.ds_meta_data.tags = ""
    return dataset


def test_get_uvlhub_doi_builds_the_external_url():
    app = create_app("testing")
    dataset = MagicMock()
    dataset.ds_meta_data.dataset_doi = "10.1234/test_doi"

    with app.app_context():
        app.config["SERVER_NAME"] = "uvlhub.io"
        result = DataSetService().get_uvlhub_doi(dataset)

    assert result == "http://uvlhub.io/doi/10.1234/test_doi"


def test_update_metadata_from_request_success():
    service = DataSetService()
    service.repository.session = MagicMock()
    service.author_repository.create = MagicMock(side_effect=lambda **kwargs: kwargs)
    service._validate_orcid = MagicMock(side_effect=["0000-0002-1825-0097", ""])
    dataset = _mock_dataset_for_edit()
    zenodo_service = MagicMock()
    zenodo_service.create_new_deposition.return_value = {"id": 101}
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

    with (
        patch.object(service, "zip_dataset", return_value="C:\\tmp\\dataset_1.zip"),
        patch("app.features.dataset.services.os.path.exists", return_value=True),
        patch("app.features.dataset.services.shutil.rmtree"),
    ):
        result = service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    assert dataset.ds_meta_data.title == "Updated dataset"
    assert dataset.ds_meta_data.tags == "tag1,tag2"
    assert dataset.ds_meta_data.dataset_anonymous is True
    assert dataset.ds_meta_data.publication_type.value == "datamanagementplan"
    assert len(dataset.ds_meta_data.authors) == 2
    assert dataset.ds_meta_data.deposition_id == 101
    assert dataset.ds_meta_data.dataset_doi == "10.5072/zenodo.101"
    assert result == {"metadata_synced": True, "sync_deferred": False}
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
            ("authors[0][orcid]", "0000-0002-1825-0097"),
            ("authors[1][name]", "Author Two"),
            ("authors[1][orcid]", "0000-0002-1825-0097"),
        ]
    )

    with pytest.raises(DatasetMetadataValidationError, match="Duplicate author detected: ORCID"):
        service.update_metadata_from_request(dataset, form_data)

    service.repository.session.rollback.assert_called_once()


def test_update_metadata_from_request_wraps_unexpected_errors():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    form_data = MultiDict([("title", "Updated dataset"), ("description", "Updated description")])

    with patch.object(service, "_replace_authors_from_form", side_effect=RuntimeError("boom")):
        with pytest.raises(DatasetMetadataUpdateError, match="boom"):
            service.update_metadata_from_request(dataset, form_data)

    service.repository.session.rollback.assert_called_once()


def test_update_metadata_from_request_duplicate_name_affiliation_without_orcid():
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


def test_update_metadata_from_request_invalid_publication_type_falls_back_to_other():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()

    form_data = MultiDict(
        [("title", "Updated dataset"), ("description", "Updated description"), ("publication_type", "not_a_valid_type")]
    )

    service.update_metadata_from_request(dataset, form_data)

    assert dataset.ds_meta_data.publication_type.name == "OTHER"
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_parses_tags_from_csv_when_tags_array_missing():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()

    form_data = MultiDict(
        [("title", "Updated dataset"), ("description", "Updated description"), ("tags", "tag1, tag2 ,tag3")]
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
        [("title", "Updated dataset"), ("description", "Updated description"), ("dataset_type", "draft")]
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

    form_data = MultiDict(
        [("title", "Updated dataset"), ("description", "Updated description"), ("dataset_type", "zenodo")]
    )

    result = service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    zenodo_service.update_deposition.assert_called_once_with(99, {"title": "Updated dataset"})
    assert result == {"metadata_synced": True, "sync_deferred": False}
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_synced_dataset_saves_locally_when_zenodo_unavailable():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    dataset.id = 42
    dataset.ds_meta_data.dataset_doi = "10.1234/demo"
    dataset.ds_meta_data.deposition_id = 99

    zenodo_service = MagicMock()
    zenodo_service.build_metadata.return_value = {"title": "Updated dataset"}
    zenodo_service.update_deposition.side_effect = ZenodoUnavailableError("Zenodo is currently unavailable.")

    form_data = MultiDict(
        [("title", "Updated dataset"), ("description", "Updated description"), ("dataset_type", "zenodo")]
    )

    result = service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    assert dataset.ds_meta_data.metadata_synced is False
    assert result == {"metadata_synced": False, "sync_deferred": True}
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_synced_dataset_without_deposition_id_raises():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = "10.1234/demo"
    dataset.ds_meta_data.deposition_id = None

    form_data = MultiDict(
        [("title", "Updated dataset"), ("description", "Updated description"), ("dataset_type", "zenodo")]
    )

    with pytest.raises(DatasetMetadataUpdateError, match="missing Zenodo deposition_id"):
        service.update_metadata_from_request(dataset, form_data, zenodo_service=MagicMock())

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

    zenodo_service = MagicMock()
    zenodo_service.create_new_deposition.return_value = {"id": 101}
    zenodo_service.get_doi.return_value = "10.5072/zenodo.101"

    with (
        patch.object(service, "zip_dataset", return_value="C:\\tmp\\dataset_1.zip"),
        patch("app.features.dataset.services.os.path.exists", return_value=True),
        patch("app.features.dataset.services.shutil.rmtree"),
    ):
        form_data = MultiDict(
            [("title", "Updated dataset"), ("description", "Updated description"), ("dataset_type", "zenodo")]
        )
        service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    zenodo_service.upload_zip.assert_called_once_with(dataset, 101, "C:\\tmp\\dataset_1.zip")
    zenodo_service.publish_deposition.assert_called_once_with(101)
    assert dataset.ds_meta_data.dataset_doi == "10.5072/zenodo.101"
    service.repository.session.commit.assert_called_once()


def test_update_metadata_from_request_unsynced_dataset_to_zenodo_fails_when_unavailable():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()

    zenodo_service = MagicMock()
    zenodo_service.create_new_deposition.side_effect = ZenodoUnavailableError("Zenodo is currently unavailable.")

    form_data = MultiDict(
        [("title", "Updated dataset"), ("description", "Updated description"), ("dataset_type", "zenodo")]
    )

    with pytest.raises(DatasetMetadataUpdateError, match="Zenodo is currently unavailable"):
        service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    service.repository.session.rollback.assert_called_once()
