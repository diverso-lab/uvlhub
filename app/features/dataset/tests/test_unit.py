import zipfile
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from app.features.dataset import routes as dataset_routes
from app.features.dataset.services import DatasetMetadataValidationError, DataSetService

pytestmark = pytest.mark.unit


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
