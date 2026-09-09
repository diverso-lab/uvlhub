import logging
import zipfile

import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
from app.features.dataset.services import DataSetService
from app.features.featuremodel.repositories import FeatureModelRepository
from app.features.featuremodel.services import FeatureModelService
from app.features.hubfile.services import HubfileService, UploadIngestService

pytestmark = pytest.mark.service


def _feature_model():
    user = UserRepository().create(email="svc@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="t", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    return FeatureModelRepository().create(dataset_id=dataset.id)


def test_create_from_file_persists_a_hubfile(test_app, clean_database, tmp_path):
    feature_model = _feature_model()
    path = tmp_path / "model.uvl"
    path.write_text("features\n    Root")

    hubfile = HubfileService().create_from_file(feature_model.id, feature_model.dataset_id, str(path))

    assert hubfile.id is not None
    assert hubfile.name == "model.uvl"
    assert hubfile.checksum


def test_create_from_file_raises_for_a_missing_file(test_app, clean_database):
    with pytest.raises(FileNotFoundError):
        HubfileService().create_from_file(1, 1, "/nonexistent/model.uvl")


def test_uploaded_folder_structure_survives_ingest_and_download(test_app, clean_database, tmp_path, monkeypatch):
    monkeypatch.setenv("WORKING_DIR", str(tmp_path))

    user = UserRepository().create(email="folders@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(title="t", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)

    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    with zipfile.ZipFile(temp_root / "models.zip", "w") as zf:
        zf.writestr("subsystems/auth/login.uvl", "features\n    Login")
        zf.writestr("subsystems/payment/checkout.uvl", "features\n    Checkout")
        zf.writestr("top.uvl", "features\n    Top")

    stage_dir, _ = UploadIngestService(logging.getLogger("test")).prepare_uvls(str(temp_root))
    FeatureModelService().create_from_uvl_files(dataset, base_dir=stage_dir)

    uvl_root = tmp_path / "uploads" / f"user_{user.id}" / f"dataset_{dataset.id}" / "uvl"
    assert (uvl_root / "subsystems" / "auth" / "login.uvl").is_file()
    assert (uvl_root / "top.uvl").is_file()

    zip_path = DataSetService().zip_from_storage(dataset, formats=["uvl"])
    with zipfile.ZipFile(zip_path) as z:
        names = set(z.namelist())

    assert "uvl/subsystems/auth/login.uvl" in names
    assert "uvl/subsystems/payment/checkout.uvl" in names
    assert "uvl/top.uvl" in names
