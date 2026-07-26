import zipfile
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest
from werkzeug.datastructures import MultiDict

from app.features.dataset import routes as dataset_routes
from app.features.dataset.services import DatasetMetadataValidationError, DataSetService

pytestmark = pytest.mark.unit


def _dataset_for_type(doi=None, anonymous=False):
    return SimpleNamespace(ds_meta_data=SimpleNamespace(dataset_doi=doi, dataset_anonymous=anonymous))


def test_current_dataset_type_is_draft_without_doi():
    assert DataSetService._current_dataset_type(_dataset_for_type(doi=None)) == "draft"


def test_current_dataset_type_is_zenodo_with_doi():
    assert DataSetService._current_dataset_type(_dataset_for_type(doi="10.5072/zenodo.1")) == "zenodo"


def test_current_dataset_type_is_anonymous_when_flagged():
    ds = _dataset_for_type(doi="10.5072/zenodo.1", anonymous=True)
    assert DataSetService._current_dataset_type(ds) == "zenodo_anonymous"


def test_validate_orcid_invalid_format():
    with pytest.raises(DatasetMetadataValidationError, match="Invalid ORCID format"):
        DataSetService()._validate_orcid("12345")


def test_validate_orcid_invalid_checksum():
    service = DataSetService()
    with patch("app.features.dataset.services.urllib_request.urlopen") as mock_urlopen:
        with pytest.raises(DatasetMetadataValidationError, match="Invalid ORCID checksum"):
            service._validate_orcid("0000-0002-1825-0096")
        mock_urlopen.assert_not_called()


def test_validate_orcid_not_found():
    service = DataSetService()
    with patch(
        "app.features.dataset.services.urllib_request.urlopen",
        side_effect=HTTPError(url="", code=404, msg="Not Found", hdrs=None, fp=None),
    ):
        with pytest.raises(DatasetMetadataValidationError, match="ORCID not found"):
            service._validate_orcid("0000-0002-1825-0097")


def test_resolve_download_formats_defaults_to_all_available():
    service = DataSetService()

    assert service.resolve_download_formats(None) == list(service.AVAILABLE_DOWNLOAD_FORMATS)


def test_resolve_download_formats_rejects_invalid_formats():
    with pytest.raises(ValueError, match="Invalid format"):
        DataSetService().resolve_download_formats(["uvl", "invalid_format"])


def test_resolve_download_formats_rejects_empty_selection():
    with pytest.raises(ValueError, match="No download formats selected"):
        DataSetService().resolve_download_formats(["   "])


def test_zip_from_storage_filters_files_by_selected_formats(tmp_path, monkeypatch):
    service = DataSetService()
    dataset = MagicMock()
    dataset.user_id = 42
    dataset.id = 99

    base = tmp_path / "uploads" / "user_42" / "dataset_99"
    (base / "uvl").mkdir(parents=True)
    (base / "glencoe").mkdir(parents=True)
    (base / "dimacs").mkdir(parents=True)
    (base / "uvl" / "model.uvl").write_text("uvl", encoding="utf-8")
    (base / "glencoe" / "model.json").write_text("json", encoding="utf-8")
    (base / "dimacs" / "model.cnf").write_text("cnf", encoding="utf-8")

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))

    zip_path = service.zip_from_storage(dataset, formats=["uvl", "dimacs"])

    with zipfile.ZipFile(zip_path, "r") as zipf:
        names = set(zipf.namelist())
    assert "uvl/model.uvl" in names
    assert "dimacs/model.cnf" in names
    assert "glencoe/model.json" not in names


def test_zip_all_datasets_by_formats_only_includes_selected_format(tmp_path, monkeypatch):
    service = DataSetService()
    monkeypatch.chdir(tmp_path)

    ds10 = tmp_path / "uploads" / "user_1" / "dataset_10"
    ds10.joinpath("uvl").mkdir(parents=True)
    ds10.joinpath("glencoe").mkdir(parents=True)
    ds10.joinpath("uvl", "a.uvl").write_text("a", encoding="utf-8")
    ds10.joinpath("glencoe", "a.json").write_text("a", encoding="utf-8")

    ds11 = tmp_path / "uploads" / "user_1" / "dataset_11"
    ds11.joinpath("glencoe").mkdir(parents=True)
    ds11.joinpath("glencoe", "b.json").write_text("b", encoding="utf-8")

    service.is_synchronized = MagicMock(side_effect=lambda dataset_id: dataset_id == 10)

    zip_path = tmp_path / "bulk.zip"
    service.zip_all_datasets_by_formats(str(zip_path), formats=["glencoe"])

    with zipfile.ZipFile(zip_path, "r") as zipf:
        names = set(zipf.namelist())
    assert "dataset_10/glencoe/a.json" in names
    assert "dataset_10/uvl/a.uvl" not in names
    assert not any(name.startswith("dataset_11/") for name in names)


def test_import_remote_uvl_to_temp_downloads_file(tmp_path):
    user = MagicMock()
    user.temp_folder.return_value = str(tmp_path / "temp")

    remote_response = MagicMock()
    remote_response.read.return_value = b"features\n    Root"
    urlopen_context = MagicMock()
    urlopen_context.__enter__.return_value = remote_response

    with patch.object(dataset_routes.urllib_request, "urlopen", return_value=urlopen_context):
        imported_file = dataset_routes._import_remote_uvl_to_temp(
            "https://www.uvlhub.io/doi/10.5281/zenodo.1/files/raw/editor_model.uvl",
            user,
        )

    assert imported_file["name"] == "editor_model.uvl"
    assert imported_file["serverFilename"].endswith("_editor_model.uvl")
    saved_path = tmp_path / "temp" / imported_file["serverFilename"]
    assert saved_path.exists()
    assert saved_path.read_text(encoding="utf-8") == "features\n    Root"


# --- Optional author data on the API upload ------------------------------


def test_normalize_authors_returns_empty_list_for_none():
    assert DataSetService().normalize_authors(None) == []


def test_normalize_authors_cleans_and_keeps_every_field():
    authors = DataSetService().normalize_authors(
        [{"name": "  Lovelace, Ada ", "affiliation": " Analytical Engine ", "orcid": "0000-0002-1825-0097"}]
    )

    assert authors == [{"name": "Lovelace, Ada", "affiliation": "Analytical Engine", "orcid": "0000-0002-1825-0097"}]


def test_normalize_authors_accepts_orcid_urls():
    authors = DataSetService().normalize_authors([{"name": "Ada", "orcid": "https://orcid.org/0000-0002-1825-0097"}])

    assert authors[0]["orcid"] == "0000-0002-1825-0097"
    assert authors[0]["affiliation"] == ""


def test_normalize_authors_validates_orcid_offline():
    # No call to orcid.org: a publication must not depend on that service.
    with patch("app.features.dataset.services.urllib_request.urlopen") as mock_urlopen:
        with pytest.raises(DatasetMetadataValidationError, match="Invalid ORCID"):
            DataSetService().normalize_authors([{"name": "Ada", "orcid": "0000-0002-1825-0096"}])
        mock_urlopen.assert_not_called()


def test_normalize_authors_requires_a_name():
    with pytest.raises(DatasetMetadataValidationError, match="must have a name"):
        DataSetService().normalize_authors([{"affiliation": "Uni"}])


def test_normalize_authors_rejects_a_non_list_payload():
    with pytest.raises(DatasetMetadataValidationError, match="list of author objects"):
        DataSetService().normalize_authors({"name": "Ada"})


def test_normalize_authors_rejects_duplicate_orcid():
    with pytest.raises(DatasetMetadataValidationError, match="Duplicate author"):
        DataSetService().normalize_authors(
            [
                {"name": "Ada", "orcid": "0000-0002-1825-0097"},
                {"name": "Ada Lovelace", "orcid": "0000-0002-1825-0097"},
            ]
        )


def test_normalize_authors_rejects_duplicate_name_and_affiliation():
    with pytest.raises(DatasetMetadataValidationError, match="same name and affiliation"):
        DataSetService().normalize_authors(
            [{"name": "Ada", "affiliation": "Uni"}, {"name": " ada ", "affiliation": "uni"}]
        )


def test_normalize_authors_rejects_too_many_authors():
    with pytest.raises(DatasetMetadataValidationError, match="Too many authors"):
        DataSetService().normalize_authors([{"name": f"Author {index}"} for index in range(26)])


def test_normalize_authors_rejects_an_oversized_name():
    with pytest.raises(DatasetMetadataValidationError, match="name is too long"):
        DataSetService().normalize_authors([{"name": "a" * 121}])


def test_extract_authors_from_request_prefers_the_json_body():
    authors = DataSetService().extract_authors_from_request({"authors": [{"name": "Ada"}]}, MultiDict())

    assert authors[0]["name"] == "Ada"


def test_extract_authors_from_request_reads_a_json_form_field():
    form_data = MultiDict([("authors", '[{"name": "Ada", "affiliation": "Uni"}]')])

    authors = DataSetService().extract_authors_from_request(None, form_data)

    assert authors == [{"name": "Ada", "affiliation": "Uni", "orcid": ""}]


def test_extract_authors_from_request_rejects_a_malformed_json_form_field():
    with pytest.raises(DatasetMetadataValidationError, match="JSON array"):
        DataSetService().extract_authors_from_request(None, MultiDict([("authors", "not json")]))


def test_extract_authors_from_request_reads_indexed_form_fields():
    form_data = MultiDict([("authors[0][name]", "Ada"), ("authors[0][affiliation]", "Uni")])

    authors = DataSetService().extract_authors_from_request(None, form_data)

    assert authors == [{"name": "Ada", "affiliation": "Uni", "orcid": ""}]


def test_extract_authors_from_request_returns_none_without_author_data():
    assert DataSetService().extract_authors_from_request({"title": "t"}, MultiDict()) is None


# --- Version lineage payloads --------------------------------------------


def _version(dataset_id, version, doi, concept_doi=None, created_at=datetime(2026, 7, 1, 10, 0, 0)):
    return SimpleNamespace(
        id=dataset_id,
        dataset_version=version,
        created_at=created_at,
        ds_meta_data=SimpleNamespace(dataset_doi=doi, dataset_concept_doi=concept_doi),
    )


def test_api_lineage_payload_marks_only_the_newest_version_as_latest():
    lineage = [
        _version(1, 1, "10.5072/zenodo.1", concept_doi="10.5072/zenodo.0"),
        _version(2, 2, "10.5072/zenodo.2", concept_doi="10.5072/zenodo.0"),
    ]

    payload = dataset_routes._api_lineage_payload(lineage)

    assert payload["concept_doi"] == "10.5072/zenodo.0"
    assert payload["total_versions"] == 2
    assert payload["latest"] == {"dataset_id": 2, "version": 2, "doi": "10.5072/zenodo.2"}
    assert [entry["is_latest"] for entry in payload["versions"]] == [False, True]


def test_api_lineage_payload_borrows_the_concept_doi_from_any_version():
    # Versions published before the concept DOI was stored keep a null column;
    # a newer sibling answers for the whole lineage.
    lineage = [_version(1, 1, "10.5072/zenodo.1"), _version(2, 2, "10.5072/zenodo.2", "10.5072/zenodo.0")]

    assert dataset_routes._api_lineage_payload(lineage)["concept_doi"] == "10.5072/zenodo.0"


def test_api_version_entry_has_no_publication_date_without_doi():
    entry = dataset_routes._api_version_entry(_version(3, 1, None), latest_id=3)

    assert entry["publication_date"] is None
    assert entry["created_at"] == "2026-07-01T10:00:00"
    assert entry["is_latest"] is True
