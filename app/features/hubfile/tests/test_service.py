import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
from app.features.featuremodel.repositories import FeatureModelRepository
from app.features.hubfile.services import HubfileService

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

    hubfile = HubfileService().create_from_file(feature_model.id, str(path))

    assert hubfile.id is not None
    assert hubfile.name == "model.uvl"
    assert hubfile.checksum


def test_create_from_file_raises_for_a_missing_file(test_app, clean_database):
    with pytest.raises(FileNotFoundError):
        HubfileService().create_from_file(1, "/nonexistent/model.uvl")
