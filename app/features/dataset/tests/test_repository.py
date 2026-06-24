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


def test_dataset_version_lineage(test_app, clean_database):
    user = UserRepository().create(email="lineage@example.com", password="pw-123456")
    repo = DataSetRepository()

    def make(version, origin_id=None):
        meta = DSMetaDataRepository().create(
            title=f"v{version}", description="d", publication_type=PublicationType.BOOK
        )
        return repo.create(
            user_id=user.id, ds_meta_data_id=meta.id, dataset_version=version, dataset_origin_id=origin_id
        )

    v1 = make(1)
    v2 = make(2, origin_id=v1.id)
    v3 = make(3, origin_id=v2.id)

    # Originals have version 1 and no origin.
    assert v1.dataset_version == 1
    assert v1.dataset_origin_id is None
    # Each version points back at the one it was derived from.
    assert v3.dataset_origin.id == v2.id
    assert v2.dataset_origin.id == v1.id
    # version_root() walks the chain back to the first version.
    assert v3.version_root().id == v1.id
    # The backref exposes the versions derived from a dataset.
    assert [d.id for d in v1.dataset_versions] == [v2.id]
