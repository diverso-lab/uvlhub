import pytest

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository

pytestmark = pytest.mark.repository


def _dataset(doi, email):
    user = UserRepository().create(email=email, password="pw-123456")
    meta = DSMetaDataRepository().create(
        title="t", description="d", publication_type=PublicationType.BOOK, dataset_doi=doi
    )
    return DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)


def test_count_synchronized_only_counts_datasets_with_a_doi(test_app, clean_database):
    _dataset(doi="10.1/sync", email="sync@example.com")
    _dataset(doi=None, email="draft@example.com")

    repo = DataSetRepository()

    assert repo.count_synchronized_datasets() == 1
    assert repo.count_unsynchronized_datasets() == 1
