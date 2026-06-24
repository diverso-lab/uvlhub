import logging
import os
import zipfile

import pytest

from app.features.hubfile.services import HubfileService, UploadIngestService

pytestmark = pytest.mark.unit


def _ingest():
    return UploadIngestService(logging.getLogger("test"))


def test_strip_uuid_prefix_removes_a_leading_uuid():
    ingest = UploadIngestService(logging.getLogger("test"))
    name = "12345678-1234-1234-1234-123456789012_model.uvl"

    assert ingest._strip_uuid_prefix(name) == "model.uvl"


def test_strip_uuid_prefix_leaves_plain_names_untouched():
    ingest = UploadIngestService(logging.getLogger("test"))

    assert ingest._strip_uuid_prefix("model.uvl") == "model.uvl"


def test_calculate_checksum_is_stable_for_the_same_content(tmp_path):
    file_a = tmp_path / "a.uvl"
    file_a.write_text("features\n    Root")
    file_b = tmp_path / "b.uvl"
    file_b.write_text("features\n    Root")

    assert HubfileService._calculate_checksum(str(file_a)) == HubfileService._calculate_checksum(str(file_b))


def test_calculate_checksum_differs_for_different_content(tmp_path):
    file_a = tmp_path / "a.uvl"
    file_a.write_text("features\n    Root")
    file_b = tmp_path / "b.uvl"
    file_b.write_text("features\n    Other")

    assert HubfileService._calculate_checksum(str(file_a)) != HubfileService._calculate_checksum(str(file_b))


def test_prepare_uvls_collects_loose_and_zipped_files(tmp_path):
    root = tmp_path / "temp"
    root.mkdir()
    (root / "a.uvl").write_text("features\n    A")
    with zipfile.ZipFile(root / "models.zip", "w") as zf:
        zf.writestr("b.uvl", "features\n    B")

    stage_dir, staged = _ingest().prepare_uvls(str(root))

    assert sorted(os.path.basename(p) for p in staged) == ["a.uvl", "b.uvl"]
    assert os.path.isdir(stage_dir)


def test_prepare_uvls_deduplicates_identical_content(tmp_path):
    root = tmp_path / "temp"
    root.mkdir()
    (root / "a.uvl").write_text("same content")
    with zipfile.ZipFile(root / "models.zip", "w") as zf:
        zf.writestr("b.uvl", "same content")  # identical bytes -> deduplicated by hash

    _, staged = _ingest().prepare_uvls(str(root))

    assert len(staged) == 1


def test_prepare_uvls_raises_when_no_uvl_files(tmp_path):
    root = tmp_path / "temp"
    root.mkdir()
    (root / "readme.txt").write_text("not a model")

    with pytest.raises(ValueError, match="No .uvl files"):
        _ingest().prepare_uvls(str(root))


def test_safe_extract_zip_rejects_path_traversal(tmp_path):
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr("../escape.uvl", "pwned")
    dest = tmp_path / "dest"
    dest.mkdir()

    with pytest.raises(ValueError, match="Zip slip"):
        _ingest()._safe_extract_zip(str(evil), str(dest))
