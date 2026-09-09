import os
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


def test_check_uvl_reports_syntax_errors_for_an_invalid_model(test_app, tmp_path):
    bad = tmp_path / "bad.uvl"
    bad.write_text("this is not a uvl model {{{\n")

    payload, status = FlamapyService().check_uvl(str(bad))

    assert status == 400
    assert payload["errors"]


def test_check_uvl_accepts_a_valid_model(test_app, tmp_path):
    good = tmp_path / "good.uvl"
    good.write_text("features\n    Root\n")

    payload, status = FlamapyService().check_uvl(str(good))

    assert status == 200
    assert "message" in payload


# ---- enqueue_missing_format_transforms (backs `rosemary formats:generate`) ----


def _hubfile_with_uvl_on_disk(tmp_path, monkeypatch, name="model.uvl"):
    from app.features.auth.repositories import UserRepository
    from app.features.dataset.models import PublicationType
    from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
    from app.features.featuremodel.repositories import FeatureModelRepository
    from app.features.hubfile.repositories import HubfileRepository

    monkeypatch.setenv("WORKING_DIR", str(tmp_path))
    user = UserRepository().create(email=f"fmt-{name}@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="t", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(feature_model_id=fm.id, dataset_id=dataset.id, name=name, size=8, checksum="x")
    uvl_path = hubfile.get_full_path()
    os.makedirs(os.path.dirname(uvl_path), exist_ok=True)
    open(uvl_path, "w").write("features")
    return hubfile, uvl_path


def _write_formats(uvl_path, formats):
    from app.features.flamapy.formats import DERIVED_FORMATS

    base = os.path.dirname(os.path.dirname(uvl_path))
    for fmt in formats:
        os.makedirs(os.path.join(base, fmt), exist_ok=True)
        stem = os.path.basename(uvl_path)[:-4]
        open(os.path.join(base, fmt, stem + DERIVED_FORMATS[fmt]), "w").write("x")


def test_enqueue_missing_formats_only_touches_hubfiles_with_a_gap(test_app, clean_database, tmp_path, monkeypatch):
    hubfile, uvl_path = _hubfile_with_uvl_on_disk(tmp_path, monkeypatch)
    _write_formats(uvl_path, ["glencoe"])  # dimacs + splot still missing

    with patch("app.features.flamapy.services.TaskQueueManager") as tqm:
        summary = FlamapyService().enqueue_missing_format_transforms(dataset_id=hubfile.dataset_id)

    tqm.return_value.enqueue_task.assert_called_once()
    _, kwargs = tqm.return_value.enqueue_task.call_args
    assert kwargs["path"] == uvl_path
    assert summary["enqueued"] == [(hubfile.id, ["dimacs", "splot"])]


def test_enqueue_missing_formats_skips_a_fully_covered_hubfile(test_app, clean_database, tmp_path, monkeypatch):
    hubfile, uvl_path = _hubfile_with_uvl_on_disk(tmp_path, monkeypatch)
    _write_formats(uvl_path, ["glencoe", "dimacs", "splot"])

    with patch("app.features.flamapy.services.TaskQueueManager") as tqm:
        summary = FlamapyService().enqueue_missing_format_transforms(dataset_id=hubfile.dataset_id)

    tqm.return_value.enqueue_task.assert_not_called()
    assert summary["up_to_date"] == 1


def test_enqueue_missing_formats_force_reprocesses_everything(test_app, clean_database, tmp_path, monkeypatch):
    hubfile, uvl_path = _hubfile_with_uvl_on_disk(tmp_path, monkeypatch)
    _write_formats(uvl_path, ["glencoe", "dimacs", "splot"])

    with patch("app.features.flamapy.services.TaskQueueManager") as tqm:
        FlamapyService().enqueue_missing_format_transforms(dataset_id=hubfile.dataset_id, force=True)

    tqm.return_value.enqueue_task.assert_called_once()


def test_enqueue_missing_formats_reports_a_hubfile_whose_uvl_is_gone(test_app, clean_database, tmp_path, monkeypatch):
    hubfile, uvl_path = _hubfile_with_uvl_on_disk(tmp_path, monkeypatch)
    os.remove(uvl_path)

    with patch("app.features.flamapy.services.TaskQueueManager") as tqm:
        summary = FlamapyService().enqueue_missing_format_transforms(dataset_id=hubfile.dataset_id)

    tqm.return_value.enqueue_task.assert_not_called()
    assert summary["missing_source"] == [hubfile.id]


def test_count_hubfiles_missing_formats(test_app, clean_database, tmp_path, monkeypatch):
    hf1, p1 = _hubfile_with_uvl_on_disk(tmp_path, monkeypatch, name="a.uvl")
    _write_formats(p1, ["glencoe", "dimacs", "splot"])
    hf2, p2 = _hubfile_with_uvl_on_disk(tmp_path, monkeypatch, name="b.uvl")
    _write_formats(p2, ["glencoe"])

    result = FlamapyService().count_hubfiles_missing_formats()

    assert result == {"pending": 1, "missing_source": 0}
