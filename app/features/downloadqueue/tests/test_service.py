import zipfile
from unittest.mock import patch

import pytest

from app.features.downloadqueue.services import DownloadqueueService

pytestmark = pytest.mark.service


class _FakeHubfile:
    def __init__(self, path):
        self._path = path

    def get_full_path(self):
        return self._path


def test_build_zip_for_ids_pulls_files_from_the_hubfile_service(test_app, tmp_path):
    uvl = tmp_path / "model.uvl"
    uvl.write_text("features")

    with patch.object(DownloadqueueService, "get_hubfiles", return_value=[_FakeHubfile(str(uvl))]):
        memory = DownloadqueueService().build_zip_for_ids([1])

    with zipfile.ZipFile(memory) as archive:
        assert archive.namelist() == ["model.uvl"]
