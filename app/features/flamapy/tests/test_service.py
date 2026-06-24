from unittest.mock import patch

import pytest

from app.features.flamapy.services import FlamapyService

pytestmark = pytest.mark.service


class _FakeHubfile:
    def __init__(self, path):
        self._path = path

    def get_path(self):
        return self._path


def test_transformed_file_path_returns_the_path_when_present(test_app, tmp_path):
    uvl_dir = tmp_path / "uvl"
    uvl_dir.mkdir()
    (uvl_dir / "model.uvl").write_text("features")
    glencoe_dir = tmp_path / "glencoe"
    glencoe_dir.mkdir()
    (glencoe_dir / "model.json").write_text("{}")

    service = FlamapyService()
    with patch.object(service.hubfile_service, "get_or_404", return_value=_FakeHubfile(str(uvl_dir / "model.uvl"))):
        path = service.transformed_file_path(1, ".json", "glencoe")

    assert path == str(glencoe_dir / "model.json")


def test_transformed_file_path_returns_none_when_missing(test_app, tmp_path):
    uvl_dir = tmp_path / "uvl"
    uvl_dir.mkdir()
    (uvl_dir / "model.uvl").write_text("features")

    service = FlamapyService()
    with patch.object(service.hubfile_service, "get_or_404", return_value=_FakeHubfile(str(uvl_dir / "model.uvl"))):
        assert service.transformed_file_path(1, ".json", "glencoe") is None


def test_check_uvl_reports_internal_error_for_a_missing_file(test_app):
    payload, status = FlamapyService().check_uvl("/nonexistent/path.uvl")

    assert status == 500
    assert "error" in payload
