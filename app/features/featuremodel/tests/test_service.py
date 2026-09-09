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


def test_create_from_uvl_files_records_the_folder_of_each_file(test_app, clean_database, tmp_path):
    import os
    import shutil

    from app.features.auth.repositories import UserRepository
    from app.features.dataset.models import PublicationType
    from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
    from app.features.hubfile.models import Hubfile

    user = UserRepository().create(email="fmfolders@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="t", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)

    stage = tmp_path / "stage"
    (stage / "subsystems" / "auth").mkdir(parents=True)
    (stage / "root.uvl").write_text("features\n    Root")
    (stage / "subsystems" / "auth" / "login.uvl").write_text("features\n    Login")

    storage_dir = os.path.join(os.getenv("WORKING_DIR", ""), "uploads", f"user_{user.id}", f"dataset_{dataset.id}")
    try:
        with patch("app.features.featuremodel.services.shutil.move", side_effect=shutil.copy2):
            models = FeatureModelService().create_from_uvl_files(dataset, base_dir=str(stage))

        assert len(models) == 2
        by_dir = {hf.directory_path: hf for hf in Hubfile.query.all()}
        assert set(by_dir) == {"", "subsystems/auth"}
        assert by_dir["subsystems/auth"].name == "login.uvl"
        assert by_dir["subsystems/auth"].relative_path == "subsystems/auth/login.uvl"
        assert (
            by_dir["subsystems/auth"].get_full_path().endswith(os.path.join("uvl", "subsystems", "auth", "login.uvl"))
        )
        assert os.path.isfile(by_dir["subsystems/auth"].get_full_path())
    finally:
        shutil.rmtree(storage_dir, ignore_errors=True)
