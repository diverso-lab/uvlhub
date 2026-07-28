from unittest.mock import MagicMock, patch

import pytest
from werkzeug.datastructures import MultiDict

from app import create_app
from app.features.dataset.services import (
    DatasetMetadataUpdateError,
    DatasetMetadataValidationError,
    DatasetOwnershipError,
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


def test_update_metadata_from_request_without_type_preserves_synced_state():
    # A POST that omits dataset_type must default to the dataset's current state,
    # not "draft": editing a synced dataset re-syncs Zenodo and keeps the DOI.
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = "10.1234/demo"
    dataset.ds_meta_data.deposition_id = 99

    zenodo_service = MagicMock()
    zenodo_service.build_metadata.return_value = {"title": "Updated dataset"}

    form_data = MultiDict([("title", "Updated dataset"), ("description", "Updated description")])

    result = service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    zenodo_service.update_deposition.assert_called_once_with(99, {"title": "Updated dataset"})
    assert dataset.ds_meta_data.dataset_doi == "10.1234/demo"
    assert result == {"metadata_synced": True, "sync_deferred": False}


def test_update_metadata_from_request_without_type_keeps_anonymous_synced_state():
    # Same guard for anonymous datasets: omitting dataset_type keeps them synced.
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = "10.1234/anon"
    dataset.ds_meta_data.deposition_id = 7
    dataset.ds_meta_data.dataset_anonymous = True

    zenodo_service = MagicMock()
    zenodo_service.build_metadata.return_value = {"title": "Anon"}

    form_data = MultiDict([("title", "Anon")])

    result = service.update_metadata_from_request(dataset, form_data, zenodo_service=zenodo_service)

    zenodo_service.update_deposition.assert_called_once_with(7, {"title": "Anon"})
    assert dataset.ds_meta_data.dataset_doi == "10.1234/anon"
    assert result == {"metadata_synced": True, "sync_deferred": False}


def test_replace_hubfile_rejects_published_dataset():
    service = DataSetService()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = "10.1234/published"

    with pytest.raises(DatasetMetadataUpdateError, match="versioned"):
        service.replace_hubfile(dataset, 1, MagicMock(filename="a.uvl"))


def test_replace_hubfile_rejects_file_not_in_dataset():
    service = DataSetService()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = None
    dataset.feature_models = []

    with pytest.raises(DatasetMetadataValidationError, match="does not belong"):
        service.replace_hubfile(dataset, 999, MagicMock(filename="a.uvl"))


def test_replace_hubfile_requires_uvl_extension():
    service = DataSetService()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = None
    hubfile = MagicMock(id=5)
    dataset.feature_models = [MagicMock(hubfiles=[hubfile])]

    with pytest.raises(DatasetMetadataValidationError, match=".uvl"):
        service.replace_hubfile(dataset, 5, MagicMock(filename="a.txt"))


def test_replace_hubfile_overwrites_content_and_resignals():
    service = DataSetService()
    service.repository.session = MagicMock()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = None
    hubfile = MagicMock(id=5)
    hubfile.get_full_path.return_value = "/data/uploads/user_1/dataset_1/uvl/m.uvl"
    dataset.feature_models = [MagicMock(hubfiles=[hubfile])]
    file_storage = MagicMock(filename="new_model.uvl")

    with (
        patch("app.features.dataset.services.os.makedirs"),
        patch("app.features.dataset.services.os.path.getsize", return_value=123),
        patch("app.features.hubfile.services.HubfileService._calculate_checksum", return_value="abc123"),
        patch("app.features.hubfile.signals.hubfile_created.send") as mock_send,
    ):
        result = service.replace_hubfile(dataset, 5, file_storage)

    file_storage.save.assert_called_once_with("/data/uploads/user_1/dataset_1/uvl/m.uvl")
    assert hubfile.checksum == "abc123"
    assert hubfile.size == 123
    service.repository.session.commit.assert_called_once()
    mock_send.assert_called_once()
    assert result is hubfile


def test_create_new_version_rejects_draft():
    service = DataSetService()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = None
    dataset.ds_meta_data.deposition_id = None

    with pytest.raises(DatasetMetadataUpdateError, match="Only published"):
        service.create_new_version(dataset, MagicMock(filename="a.uvl"), MagicMock(), zenodo_service=MagicMock())


def test_create_new_version_requires_uvl_extension():
    service = DataSetService()
    dataset = _mock_dataset_for_edit()
    dataset.ds_meta_data.dataset_doi = "10.5072/zenodo.1"
    dataset.ds_meta_data.deposition_id = 111

    with pytest.raises(DatasetMetadataValidationError, match=".uvl"):
        service.create_new_version(dataset, MagicMock(filename="a.txt"), MagicMock(), zenodo_service=MagicMock())


def test_create_new_version_creates_linked_dataset(test_app, clean_database):
    import io

    from werkzeug.datastructures import FileStorage

    from app.features.auth.repositories import UserRepository
    from app.features.dataset.models import PublicationType
    from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository

    user = UserRepository().create(email="version@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(
        title="Original",
        description="d",
        publication_type=PublicationType.BOOK,
        dataset_doi="10.5072/zenodo.111",
        deposition_id=111,
    )
    old = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id, dataset_version=1)

    zenodo = MagicMock()
    zenodo.create_new_version_draft.return_value = 222
    zenodo.build_metadata.return_value = {"title": "Original", "version": "2"}
    zenodo.get_doi.return_value = "10.5072/zenodo.222"

    file_storage = FileStorage(
        stream=io.BytesIO(b"features\n    Root\n        mandatory\n            A\n"), filename="v2.uvl"
    )

    new = DataSetService().create_new_version(old, file_storage, user, zenodo_service=zenodo)

    assert new.id != old.id
    assert new.dataset_version == 2
    assert new.dataset_origin_id == old.id
    assert new.ds_meta_data.dataset_doi == "10.5072/zenodo.222"
    assert new.ds_meta_data.deposition_id == 222
    zenodo.create_new_version_draft.assert_called_once_with(111)
    zenodo.delete_all_deposition_files.assert_called_once_with(222)
    zenodo.publish_deposition.assert_called_once_with(222)


def _uvl_upload(name="v2.uvl"):
    import io

    from werkzeug.datastructures import FileStorage

    return FileStorage(stream=io.BytesIO(b"features\n    Root\n        mandatory\n            A\n"), filename=name)


def test_create_new_version_refuses_a_dataset_that_is_already_superseded(test_app, clean_database):
    # Two /new-version calls against the same node (a client retry after a
    # timeout, a duplicated job, a stale dataset id) would create two children
    # claiming the same predecessor. Nothing downstream could then answer
    # "which one is the newest version", and a transfer would move one branch
    # and leave the other behind.
    owner, (v1, v2) = _make_lineage("supersede@example.com")
    zenodo = MagicMock()

    with pytest.raises(DatasetMetadataUpdateError, match="already been superseded"):
        DataSetService().create_new_version(v1, _uvl_upload(), owner, zenodo_service=zenodo)

    zenodo.create_new_version_draft.assert_not_called()
    assert [dataset.id for dataset in v1.all_versions()] == [v1.id, v2.id]


def test_create_new_version_removes_the_clone_when_zenodo_fails(test_app, clean_database, tmp_path, monkeypatch):
    # The clone is committed before Zenodo is called, so a failure has to take
    # it back out. An abandoned clone would sit in the lineage forever with no
    # DOI, and the lineage endpoints would advertise it as the newest version.
    from app.features.dataset.repositories import DataSetRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1,) = _make_lineage("orphan-clone@example.com", versions=1)
    zenodo = MagicMock()
    zenodo.create_new_version_draft.side_effect = RuntimeError("Zenodo returned 502")

    with pytest.raises(RuntimeError, match="502"):
        DataSetService().create_new_version(v1, _uvl_upload(), owner, zenodo_service=zenodo)

    repository = DataSetRepository()
    assert repository.model.query.count() == 1
    surviving = repository.get_by_id(v1.id)
    assert [dataset.id for dataset in surviving.all_versions()] == [v1.id]
    assert surviving.is_latest_version() is True


def _zenodo_that_publishes(deposition_id=999):
    zenodo = MagicMock()
    zenodo.create_new_version_draft.return_value = deposition_id
    zenodo.build_metadata.return_value = {"title": "x"}
    return zenodo


def test_create_new_version_keeps_the_clone_when_the_doi_read_fails_after_publishing(
    test_app, clean_database, tmp_path, monkeypatch
):
    # publish_deposition mints a permanent public DOI. Nothing after it may
    # delete the local row: the Zenodo record holds the user's files and cannot
    # be withdrawn, so erasing the only local pointer to it strands it forever.
    # The cleanup used to run here and take the row, its metadata and its files
    # with it, leaving deposition 999 recorded nowhere at all.
    from app.features.dataset.repositories import DataSetRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1,) = _make_lineage("published-orphan@example.com", versions=1)
    zenodo = _zenodo_that_publishes()
    zenodo.get_doi.side_effect = RuntimeError("read timed out")

    with pytest.raises(RuntimeError, match="timed out"):
        DataSetService().create_new_version(v1, _uvl_upload(), owner, zenodo_service=zenodo)

    assert zenodo.publish_deposition.call_count == 1

    repository = DataSetRepository()
    assert repository.model.query.count() == 2
    survivor = [dataset for dataset in repository.model.query.all() if dataset.id != v1.id][0]
    # The deposition id is the handle that makes reconciliation possible.
    assert survivor.ds_meta_data.deposition_id == 999
    assert survivor.ds_meta_data.dataset_doi is None


def test_create_new_version_keeps_the_clone_when_zenodo_returns_no_doi_after_publishing(
    test_app, clean_database, tmp_path, monkeypatch
):
    # Same point of no return, reached through the empty-DOI guard instead of
    # an exception from the client.
    from app.features.dataset.repositories import DataSetRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1,) = _make_lineage("published-nodoi@example.com", versions=1)
    zenodo = _zenodo_that_publishes()
    zenodo.get_doi.return_value = ""

    with pytest.raises(DatasetMetadataUpdateError, match="did not return a DOI"):
        DataSetService().create_new_version(v1, _uvl_upload(), owner, zenodo_service=zenodo)

    assert zenodo.publish_deposition.call_count == 1

    repository = DataSetRepository()
    assert repository.model.query.count() == 2
    survivor = [dataset for dataset in repository.model.query.all() if dataset.id != v1.id][0]
    assert survivor.ds_meta_data.deposition_id == 999


def test_create_new_version_records_the_deposition_before_publishing(test_app, clean_database, tmp_path, monkeypatch):
    # The deposition id has to be committed before the irreversible call, not
    # after it. If publish_deposition itself dies mid-flight the caller cannot
    # know whether the record went public, and only a persisted deposition id
    # lets anyone find out.
    from app.features.dataset.repositories import DataSetRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1,) = _make_lineage("deposition-first@example.com", versions=1)

    seen = {}

    def _capture(deposition_id):
        rows = DataSetRepository().model.query.all()
        seen["deposition_ids"] = [row.ds_meta_data.deposition_id for row in rows]
        raise RuntimeError("connection reset while publishing")

    zenodo = _zenodo_that_publishes()
    zenodo.publish_deposition.side_effect = _capture

    with pytest.raises(RuntimeError, match="connection reset"):
        DataSetService().create_new_version(v1, _uvl_upload(), owner, zenodo_service=zenodo)

    # Visible in the database at the moment publish was attempted.
    assert 999 in seen["deposition_ids"]
    # And still there afterwards, because a row Zenodo has seen is never discarded.
    repository = DataSetRepository()
    assert 999 in [row.ds_meta_data.deposition_id for row in repository.model.query.all()]


def test_discard_unpublished_version_refuses_a_row_that_names_a_deposition(
    test_app, clean_database, tmp_path, monkeypatch
):
    # The structural guard, tested directly. Whatever calls it, a row carrying
    # a deposition id is a row Zenodo knows about and must not be deleted.
    from app.features.dataset.repositories import DataSetRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    _, (v1,) = _make_lineage("guard@example.com", versions=1)

    DataSetService()._discard_unpublished_version(v1)

    assert DataSetRepository().get_by_id(v1.id) is not None


def test_clone_does_not_inherit_the_concept_doi_of_its_origin(test_app, clean_database):
    # Zenodo decides which concept a deposition belongs to, and it has not been
    # asked yet. A copied value would be a wrong, permanent concept DOI on any
    # clone that ends up in a deposition of its own.
    owner, (v1,) = _make_lineage("clone-concept@example.com", versions=1, concept_doi="10.5072/zenodo.10")

    clone = DataSetService()._clone_as_new_version(v1, owner)

    assert clone.ds_meta_data.dataset_concept_doi is None
    assert clone.dataset_origin_id == v1.id
    assert clone.dataset_version == 2


def test_publishing_a_clone_stores_the_concept_doi_zenodo_actually_gave_it(test_app, clean_database):
    # A dataset must never advertise a concept DOI that is not the concept
    # Zenodo put it in: resolving it would never return this record.
    owner, (v1,) = _make_lineage("clone-publish@example.com", versions=1, concept_doi="10.5072/zenodo.10")
    service = DataSetService()
    clone = service._clone_as_new_version(v1, owner)
    clone.ds_meta_data.dataset_doi = None
    clone.ds_meta_data.deposition_id = None

    zenodo = MagicMock()
    zenodo.create_new_deposition.return_value = {"id": 99}
    zenodo.get_doi.return_value = "10.5072/zenodo.99"
    zenodo.get_concept_doi.return_value = "10.5072/zenodo.98"

    with (
        patch.object(service, "zip_dataset", return_value="/tmp/dataset_clone.zip"),
        patch("app.features.dataset.services.os.path.exists", return_value=False),
    ):
        service._publish_dataset_to_zenodo(clone, zenodo)

    assert clone.ds_meta_data.dataset_doi == "10.5072/zenodo.99"
    assert clone.ds_meta_data.dataset_concept_doi == "10.5072/zenodo.98"


# --- Concept DOI ---------------------------------------------------------


def _make_lineage(email, versions=2, concept_doi=None, user=None):
    """Create a real published lineage in the database, oldest first."""
    from app.features.auth.repositories import UserRepository
    from app.features.dataset.models import PublicationType
    from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository

    owner = user or UserRepository().create(email=email, password="pw-123456")
    created = []
    origin_id = None
    for version in range(1, versions + 1):
        meta = DSMetaDataRepository().create(
            title=f"v{version}",
            description="d",
            publication_type=PublicationType.BOOK,
            dataset_doi=f"10.5072/zenodo.{version}",
            dataset_concept_doi=concept_doi,
            deposition_id=version,
        )
        dataset = DataSetRepository().create(
            user_id=owner.id, ds_meta_data_id=meta.id, dataset_version=version, dataset_origin_id=origin_id
        )
        created.append(dataset)
        origin_id = dataset.id
    return owner, created


def test_store_concept_doi_backfills_every_version_of_the_lineage(test_app, clean_database):
    _, (v1, v2) = _make_lineage("concept-store@example.com")

    DataSetService().store_concept_doi(v2, "10.5072/zenodo.0")

    assert v1.ds_meta_data.dataset_concept_doi == "10.5072/zenodo.0"
    assert v2.ds_meta_data.dataset_concept_doi == "10.5072/zenodo.0"


def test_store_concept_doi_overwrites_the_value_of_the_dataset_it_is_given(test_app, clean_database):
    # The value comes from the deposition this dataset actually points at, so
    # it is the authoritative answer for this row. A stale value inherited from
    # somewhere else would advertise a Zenodo concept the record is not in, and
    # nothing else would ever correct it.
    _, (v1, v2) = _make_lineage("concept-keep@example.com", concept_doi="10.5072/zenodo.0")

    DataSetService().store_concept_doi(v2, "10.5072/zenodo.999")

    assert v2.ds_meta_data.dataset_concept_doi == "10.5072/zenodo.999"
    # A sibling that already carries a different value belongs to a different
    # Zenodo concept: that is a real state, so it is logged, not rewritten.
    assert v1.ds_meta_data.dataset_concept_doi == "10.5072/zenodo.0"


def test_resolve_and_store_concept_doi_survives_a_failure_to_persist(test_app, clean_database):
    # By the time this runs the version DOI is minted at Zenodo and committed
    # locally. A lock timeout on the UPDATE must not turn a successful
    # publication into an error for the client.
    _, (v1,) = _make_lineage("concept-crash@example.com", versions=1)
    service = DataSetService()
    zenodo = MagicMock()
    zenodo.get_concept_doi.return_value = "10.5072/zenodo.0"

    with patch.object(service, "store_concept_doi", side_effect=RuntimeError("lock wait timeout")):
        assert service.resolve_and_store_concept_doi(v1, zenodo, 1) is None

    # The session is left clean, so the caller can keep using it.
    assert service.repository.get_by_id(v1.id) is not None


def test_resolve_and_store_concept_doi_persists_the_zenodo_value(test_app, clean_database):
    _, (v1,) = _make_lineage("concept-resolve@example.com", versions=1)
    zenodo = MagicMock()
    zenodo.get_concept_doi.return_value = "10.5072/zenodo.0"

    result = DataSetService().resolve_and_store_concept_doi(v1, zenodo, 1)

    assert result == "10.5072/zenodo.0"
    assert v1.ds_meta_data.dataset_concept_doi == "10.5072/zenodo.0"


def test_resolve_and_store_concept_doi_uses_the_fallback_when_zenodo_fails(test_app, clean_database):
    # Publishing already succeeded, so a Zenodo error must not lose the lineage.
    _, (v1,) = _make_lineage("concept-fallback@example.com", versions=1)
    zenodo = MagicMock()
    zenodo.get_concept_doi.side_effect = RuntimeError("Zenodo is down")

    result = DataSetService().resolve_and_store_concept_doi(v1, zenodo, 1, fallback="10.5072/zenodo.0")

    assert result == "10.5072/zenodo.0"
    assert v1.ds_meta_data.dataset_concept_doi == "10.5072/zenodo.0"


def test_resolve_and_store_concept_doi_leaves_the_column_null_when_unavailable(test_app, clean_database):
    _, (v1,) = _make_lineage("concept-none@example.com", versions=1)
    zenodo = MagicMock()
    zenodo.get_concept_doi.return_value = None

    assert DataSetService().resolve_and_store_concept_doi(v1, zenodo, 1) is None
    assert v1.ds_meta_data.dataset_concept_doi is None


def test_publishing_stores_the_concept_doi(test_app, clean_database):
    _, (dataset,) = _make_lineage("concept-publish@example.com", versions=1)
    dataset.ds_meta_data.dataset_doi = None
    dataset.ds_meta_data.deposition_id = None
    service = DataSetService()
    zenodo = MagicMock()
    zenodo.create_new_deposition.return_value = {"id": 101}
    zenodo.get_doi.return_value = "10.5072/zenodo.101"
    zenodo.get_concept_doi.return_value = "10.5072/zenodo.100"

    with (
        patch.object(service, "zip_dataset", return_value="/tmp/dataset_1.zip"),
        patch("app.features.dataset.services.os.path.exists", return_value=False),
    ):
        service._publish_dataset_to_zenodo(dataset, zenodo)

    assert dataset.ds_meta_data.dataset_doi == "10.5072/zenodo.101"
    assert dataset.ds_meta_data.dataset_concept_doi == "10.5072/zenodo.100"


def test_create_new_version_shares_the_concept_doi_with_its_origin(test_app, clean_database):
    import io

    from werkzeug.datastructures import FileStorage

    owner, (old,) = _make_lineage("concept-version@example.com", versions=1)
    zenodo = MagicMock()
    zenodo.create_new_version_draft.return_value = 222
    zenodo.build_metadata.return_value = {"title": "v1", "version": "2"}
    zenodo.get_doi.return_value = "10.5072/zenodo.222"
    zenodo.get_concept_doi.return_value = "10.5072/zenodo.0"

    file_storage = FileStorage(
        stream=io.BytesIO(b"features\n    Root\n        mandatory\n            A\n"), filename="v2.uvl"
    )

    new = DataSetService().create_new_version(old, file_storage, owner, zenodo_service=zenodo)

    assert new.ds_meta_data.dataset_concept_doi == "10.5072/zenodo.0"
    # The older version is backfilled, so the whole lineage shares one handle.
    assert old.ds_meta_data.dataset_concept_doi == "10.5072/zenodo.0"


# --- Lineage resolution ---------------------------------------------------


def test_get_lineage_by_concept_doi_returns_the_chain_oldest_first(test_app, clean_database):
    _, (v1, v2, v3) = _make_lineage("lineage-concept@example.com", versions=3, concept_doi="10.5072/zenodo.0")

    lineage = DataSetService().get_lineage_by_concept_doi("10.5072/zenodo.0")

    assert [dataset.id for dataset in lineage] == [v1.id, v2.id, v3.id]


def test_get_lineage_by_concept_doi_is_empty_when_unknown(test_app, clean_database):
    _make_lineage("lineage-unknown@example.com", versions=1, concept_doi="10.5072/zenodo.0")

    assert DataSetService().get_lineage_by_concept_doi("10.5072/zenodo.404") == []


def test_get_lineage_by_concept_doi_keeps_versions_that_predate_the_column(test_app, clean_database):
    _, (v1, v2) = _make_lineage("lineage-legacy@example.com", versions=2)
    v2.ds_meta_data.dataset_concept_doi = "10.5072/zenodo.0"

    lineage = DataSetService().get_lineage_by_concept_doi("10.5072/zenodo.0")

    assert [dataset.id for dataset in lineage] == [v1.id, v2.id]


def test_get_lineage_by_concept_doi_leaves_out_a_version_from_another_concept(test_app, clean_database):
    # Resolving this concept DOI at Zenodo will never return a version that
    # ended up in a different concept, so naming it here (and, being the
    # newest, calling it the latest) would contradict the record the endpoint
    # exists to point at.
    _, (v1, v2) = _make_lineage("lineage-divergent@example.com", versions=2)
    v1.ds_meta_data.dataset_concept_doi = "10.5072/zenodo.10"
    v2.ds_meta_data.dataset_concept_doi = "10.5072/zenodo.20"
    service = DataSetService()

    assert [dataset.id for dataset in service.get_lineage_by_concept_doi("10.5072/zenodo.10")] == [v1.id]
    assert [dataset.id for dataset in service.get_lineage_by_concept_doi("10.5072/zenodo.20")] == [v2.id]


# --- Ownership transfer ---------------------------------------------------


def _dataset_dir(root, user_id, dataset_id):
    import os

    return os.path.join(str(root), "uploads", f"user_{user_id}", f"dataset_{dataset_id}")


def _seed_storage(root, user_id, dataset_id, content="features\n    Root"):
    import os

    uvl_dir = os.path.join(_dataset_dir(root, user_id, dataset_id), "uvl")
    os.makedirs(uvl_dir, exist_ok=True)
    with open(os.path.join(uvl_dir, "model.uvl"), "w", encoding="utf-8") as handle:
        handle.write(content)


def test_transfer_ownership_moves_the_whole_lineage_and_its_files(test_app, clean_database, tmp_path, monkeypatch):
    import os

    from app.features.auth.repositories import UserRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1, v2) = _make_lineage("transfer-from@example.com")
    service_account = UserRepository().create(email="transfer-to@example.com", password="pw-123456")
    _seed_storage(tmp_path, owner.id, v1.id)
    _seed_storage(tmp_path, owner.id, v2.id)

    lineage = DataSetService().transfer_ownership(v2, service_account)

    assert [dataset.id for dataset in lineage] == [v1.id, v2.id]
    assert v1.user_id == service_account.id
    assert v2.user_id == service_account.id
    for dataset in (v1, v2):
        assert os.path.isdir(_dataset_dir(tmp_path, service_account.id, dataset.id))
        assert not os.path.exists(_dataset_dir(tmp_path, owner.id, dataset.id))
    # Files stay reachable: the stored path follows the new owner.
    assert os.path.exists(os.path.join(_dataset_dir(tmp_path, service_account.id, v1.id), "uvl", "model.uvl"))


def test_transfer_ownership_works_without_files_on_disk(test_app, clean_database, tmp_path, monkeypatch):
    from app.features.auth.repositories import UserRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    _, (v1,) = _make_lineage("transfer-nofiles@example.com", versions=1)
    service_account = UserRepository().create(email="transfer-nofiles-to@example.com", password="pw-123456")

    DataSetService().transfer_ownership(v1, service_account)

    assert v1.user_id == service_account.id


def test_transfer_ownership_rejects_the_current_owner(test_app, clean_database, tmp_path, monkeypatch):
    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1,) = _make_lineage("transfer-self@example.com", versions=1)

    with pytest.raises(DatasetOwnershipError, match="already belongs"):
        DataSetService().transfer_ownership(v1, owner)


def test_transfer_ownership_refuses_a_lineage_split_across_accounts(test_app, clean_database, tmp_path, monkeypatch):
    from app.features.auth.repositories import UserRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1, v2) = _make_lineage("transfer-split@example.com")
    other = UserRepository().create(email="transfer-split-other@example.com", password="pw-123456")
    target = UserRepository().create(email="transfer-split-target@example.com", password="pw-123456")
    v1.user_id = other.id

    with pytest.raises(DatasetOwnershipError, match="split across several accounts"):
        DataSetService().transfer_ownership(v2, target)

    assert v2.user_id == owner.id


def test_transfer_ownership_moves_every_branch_of_a_split_lineage(test_app, clean_database, tmp_path, monkeypatch):
    # Legacy rows can have two children of the same node. Moving only the first
    # branch would leave published versions, each with a permanent DOI, behind
    # with the previous owner, and neither account could version the record
    # afterwards.
    import os

    from app.features.auth.repositories import UserRepository
    from app.features.dataset.models import PublicationType
    from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1,) = _make_lineage("split-branch@example.com", versions=1)
    target = UserRepository().create(email="split-branch-to@example.com", password="pw-123456")

    def child(doi):
        meta = DSMetaDataRepository().create(
            title="branch",
            description="d",
            publication_type=PublicationType.BOOK,
            dataset_doi=doi,
            deposition_id=2,
        )
        return DataSetRepository().create(
            user_id=owner.id, ds_meta_data_id=meta.id, dataset_version=2, dataset_origin_id=v1.id
        )

    branch_a = child("10.5072/zenodo.201")
    branch_b = child("10.5072/zenodo.202")
    for dataset in (v1, branch_a, branch_b):
        _seed_storage(tmp_path, owner.id, dataset.id)

    moved = DataSetService().transfer_ownership(branch_b, target)

    assert [dataset.id for dataset in moved] == [v1.id, branch_a.id, branch_b.id]
    for dataset in (v1, branch_a, branch_b):
        assert dataset.user_id == target.id
        assert os.path.isdir(_dataset_dir(tmp_path, target.id, dataset.id))
        assert not os.path.exists(_dataset_dir(tmp_path, owner.id, dataset.id))


# --- Ownership transfer consent -------------------------------------------


def test_request_ownership_transfer_moves_nothing_until_it_is_accepted(test_app, clean_database, tmp_path, monkeypatch):
    # A dataset carries a permanent Zenodo DOI and shows up in its owner's
    # public listings, so an account that never asked for it must be able to
    # refuse.
    from app.features.auth.repositories import UserRepository
    from app.features.dataset.models import DatasetTransferStatus

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1, v2) = _make_lineage("offer-from@example.com")
    recipient = UserRepository().create(email="offer-to@example.com", password="pw-123456")

    with patch("app.features.mail.services.MailService") as mail_service:
        transfer = DataSetService().request_ownership_transfer(v1, owner, recipient, message="please take it")

    assert transfer.status == DatasetTransferStatus.PENDING
    assert transfer.to_user_id == recipient.id
    assert v1.user_id == owner.id
    assert v2.user_id == owner.id
    mail_service.return_value.send_email.assert_called_once()


def test_accept_ownership_transfer_moves_the_whole_lineage(test_app, clean_database, tmp_path, monkeypatch):
    from app.features.auth.repositories import UserRepository
    from app.features.dataset.models import DatasetTransferStatus

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1, v2) = _make_lineage("accept-from@example.com")
    recipient = UserRepository().create(email="accept-to@example.com", password="pw-123456")
    service = DataSetService()

    with patch("app.features.mail.services.MailService"):
        transfer = service.request_ownership_transfer(v1, owner, recipient)
        lineage = service.accept_ownership_transfer(transfer, recipient)

    assert [dataset.id for dataset in lineage] == [v1.id, v2.id]
    assert v1.user_id == recipient.id
    assert v2.user_id == recipient.id
    assert transfer.status == DatasetTransferStatus.ACCEPTED
    assert transfer.resolved_at is not None


def test_declined_transfer_leaves_the_dataset_where_it_was(test_app, clean_database, tmp_path, monkeypatch):
    from app.features.auth.repositories import UserRepository
    from app.features.dataset.models import DatasetTransferStatus

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1,) = _make_lineage("decline-from@example.com", versions=1)
    recipient = UserRepository().create(email="decline-to@example.com", password="pw-123456")
    service = DataSetService()

    with patch("app.features.mail.services.MailService"):
        transfer = service.request_ownership_transfer(v1, owner, recipient)
        service.decline_ownership_transfer(transfer, recipient)

    assert transfer.status == DatasetTransferStatus.DECLINED
    assert v1.user_id == owner.id

    with pytest.raises(DatasetOwnershipError, match="already declined"):
        service.accept_ownership_transfer(transfer, recipient)


def test_only_the_receiving_account_can_accept_a_transfer(test_app, clean_database, tmp_path, monkeypatch):
    from app.features.auth.repositories import UserRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1,) = _make_lineage("wrong-accept-from@example.com", versions=1)
    recipient = UserRepository().create(email="wrong-accept-to@example.com", password="pw-123456")
    stranger = UserRepository().create(email="wrong-accept-stranger@example.com", password="pw-123456")
    service = DataSetService()

    with patch("app.features.mail.services.MailService"):
        transfer = service.request_ownership_transfer(v1, owner, recipient)

    with pytest.raises(DatasetOwnershipError, match="Only the account the dataset was offered to"):
        service.accept_ownership_transfer(transfer, stranger)

    assert v1.user_id == owner.id


def test_a_second_offer_on_the_same_lineage_is_refused(test_app, clean_database, tmp_path, monkeypatch):
    from app.features.auth.repositories import UserRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1, v2) = _make_lineage("double-offer@example.com")
    first = UserRepository().create(email="double-offer-one@example.com", password="pw-123456")
    second = UserRepository().create(email="double-offer-two@example.com", password="pw-123456")
    service = DataSetService()

    with patch("app.features.mail.services.MailService"):
        service.request_ownership_transfer(v1, owner, first)
        with pytest.raises(DatasetOwnershipError, match="already pending"):
            # Any member of the lineage blocks the next offer: the whole chain
            # travels together.
            service.request_ownership_transfer(v2, owner, second)


def test_a_cancelled_offer_can_no_longer_be_accepted(test_app, clean_database, tmp_path, monkeypatch):
    from app.features.auth.repositories import UserRepository
    from app.features.dataset.models import DatasetTransferStatus

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1,) = _make_lineage("cancel-from@example.com", versions=1)
    recipient = UserRepository().create(email="cancel-to@example.com", password="pw-123456")
    service = DataSetService()

    with patch("app.features.mail.services.MailService"):
        transfer = service.request_ownership_transfer(v1, owner, recipient)
    service.cancel_ownership_transfer(transfer, owner)

    assert transfer.status == DatasetTransferStatus.CANCELLED
    with pytest.raises(DatasetOwnershipError, match="already cancelled"):
        service.accept_ownership_transfer(transfer, recipient)
    assert v1.user_id == owner.id


def test_transfer_ownership_restores_the_files_it_moved_when_it_fails(test_app, clean_database, tmp_path, monkeypatch):
    import os

    from app.features.auth.repositories import UserRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    owner, (v1, v2) = _make_lineage("transfer-rollback@example.com")
    target = UserRepository().create(email="transfer-rollback-to@example.com", password="pw-123456")
    _seed_storage(tmp_path, owner.id, v1.id)
    _seed_storage(tmp_path, owner.id, v2.id)
    # The target already holds a directory for the second version: half a
    # lineage must never be left behind, so the first move is undone.
    os.makedirs(_dataset_dir(tmp_path, target.id, v2.id))

    with pytest.raises(DatasetOwnershipError, match="already has storage"):
        DataSetService().transfer_ownership(v1, target)

    assert os.path.isdir(_dataset_dir(tmp_path, owner.id, v1.id))
    assert os.path.isdir(_dataset_dir(tmp_path, owner.id, v2.id))
    assert v1.user_id == owner.id
    assert v2.user_id == owner.id


# --- Admin cleanup command -------------------------------------------------


def _load_rosemary_command(module_name):
    """Load a rosemary command by path.

    `rosemary` resolves to the repository directory as a namespace package, so
    the real command modules under rosemary/src are not importable by name.
    """
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[4] / "rosemary" / "src" / "rosemary" / "commands" / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_db_delete_dataset_removes_a_dataset_that_was_offered(test_app, clean_database, tmp_path, monkeypatch):
    # The command deleted views, downloads, authors and hubfiles but never the
    # ownership transfer offers, so it aborted with foreign key error 1451 on
    # any dataset that had ever been offered, including a declined offer.
    from datetime import datetime

    from click.testing import CliRunner

    from app import db
    from app.features.dataset.models import DatasetTransferRequest, DatasetTransferStatus
    from app.features.dataset.repositories import DataSetRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    command = _load_rosemary_command("db_delete_dataset")

    owner, (dataset,) = _make_lineage("cleanup-owner@example.com", versions=1)
    doi = dataset.ds_meta_data.dataset_doi
    dataset_id = dataset.id

    from app.features.auth.repositories import UserRepository

    recipient = UserRepository().create(email="cleanup-recipient@example.com", password="pw-123456")
    db.session.add(
        DatasetTransferRequest(
            dataset_id=dataset_id,
            from_user_id=owner.id,
            to_user_id=recipient.id,
            status=DatasetTransferStatus.DECLINED,
            created_at=datetime(2026, 1, 1),
        )
    )
    db.session.commit()

    with (
        patch.object(command, "create_app", return_value=test_app),
        patch.object(command, "ElasticsearchService") as elasticsearch,
    ):
        elasticsearch.return_value = MagicMock()
        result = CliRunner().invoke(command.delete_dataset, [doi, "--yes"])

    assert result.exit_code == 0, result.output
    assert "deleted successfully" in result.output
    assert DataSetRepository().get_by_id(dataset_id) is None
    assert DatasetTransferRequest.query.filter_by(dataset_id=dataset_id).count() == 0
