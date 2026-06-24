import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
from app.features.featuremodel.repositories import FeatureModelRepository
from app.features.hubfile.repositories import HubfileRepository

pytestmark = pytest.mark.repository


def _make_hubfile(name="model.uvl", email="owner@example.com"):
    user = UserRepository().create(email=email, password="pw-123456")
    meta = DSMetaDataRepository().create(title="t", description="d", publication_type=PublicationType.BOOK)
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)
    fm = FeatureModelRepository().create(dataset_id=dataset.id)
    hubfile = HubfileRepository().create(
        name=name, checksum="abc", size=10, feature_model_id=fm.id, dataset_id=dataset.id
    )
    return hubfile, user, dataset


def test_get_by_ids_returns_empty_for_no_ids(test_app, clean_database):
    assert HubfileRepository().get_by_ids([]) == []


def test_get_by_ids_returns_matching_hubfiles(test_app, clean_database):
    hubfile, _, _ = _make_hubfile()

    found = HubfileRepository().get_by_ids([hubfile.id])

    assert [h.id for h in found] == [hubfile.id]


def test_get_owner_user_by_hubfile(test_app, clean_database):
    hubfile, user, _ = _make_hubfile()

    assert HubfileRepository().get_owner_user_by_hubfile(hubfile).id == user.id


def test_get_dataset_by_hubfile(test_app, clean_database):
    hubfile, _, dataset = _make_hubfile()

    assert HubfileRepository().get_dataset_by_hubfile(hubfile).id == dataset.id
