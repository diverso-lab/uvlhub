from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.features.featuremodel.services import FeatureModelService

pytestmark = pytest.mark.service


def test_count_feature_models_is_zero_on_an_empty_database(test_app, clean_database):
    assert FeatureModelService().count_feature_models() == 0


def test_create_from_uvl_files_creates_one_model_per_uvl(test_app, tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.uvl").write_text("features")
    (source / "ignore.txt").write_text("noise")

    service = FeatureModelService()
    dataset = SimpleNamespace(id=2, user=SimpleNamespace(id=1))

    with (
        patch("app.features.featuremodel.services.shutil.move"),
        patch.object(service.repository, "create", return_value=SimpleNamespace(id=10)) as create,
        patch.object(service.hubfile_service, "create_from_file", return_value=SimpleNamespace(id=99)),
    ):
        models = service.create_from_uvl_files(dataset, base_dir=str(source))

    assert len(models) == 1
    create.assert_called_once_with(commit=False, dataset_id=2)
