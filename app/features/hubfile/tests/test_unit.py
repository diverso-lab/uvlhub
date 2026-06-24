import logging

import pytest

from app.features.hubfile.services import HubfileService, UploadIngestService

pytestmark = pytest.mark.unit


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
