import zipfile

import pytest

from app.features.downloadqueue.services import DownloadqueueService

pytestmark = pytest.mark.unit


class _FakeHubfile:
    def __init__(self, path):
        self._path = path

    def get_full_path(self):
        return self._path


def test_parse_file_ids_extracts_integers():
    assert DownloadqueueService.parse_file_ids("1,2,3") == [1, 2, 3]


def test_parse_file_ids_ignores_blank_tokens():
    assert DownloadqueueService.parse_file_ids("1,,2, ,3") == [1, 2, 3]


def test_parse_file_ids_of_empty_string():
    assert DownloadqueueService.parse_file_ids("") == []


def test_build_zip_includes_existing_files(tmp_path):
    first = tmp_path / "a.uvl"
    first.write_text("feature A")
    second = tmp_path / "b.uvl"
    second.write_text("feature B")

    memory = DownloadqueueService.build_zip([_FakeHubfile(str(first)), _FakeHubfile(str(second))])

    with zipfile.ZipFile(memory) as archive:
        assert sorted(archive.namelist()) == ["a.uvl", "b.uvl"]


def test_build_zip_skips_missing_files(tmp_path):
    existing = tmp_path / "a.uvl"
    existing.write_text("x")
    missing = _FakeHubfile(str(tmp_path / "ghost.uvl"))

    memory = DownloadqueueService.build_zip([_FakeHubfile(str(existing)), missing])

    with zipfile.ZipFile(memory) as archive:
        assert archive.namelist() == ["a.uvl"]
