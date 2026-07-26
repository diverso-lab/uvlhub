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
    # all_versions() returns the whole chain oldest-first from any node.
    assert [d.id for d in v3.all_versions()] == [v1.id, v2.id, v3.id]
    assert [d.id for d in v1.all_versions()] == [v1.id, v2.id, v3.id]
    assert v1.has_versions() is True
    assert v3.has_versions() is True


def test_get_synchronized_by_user_returns_only_latest_versions(test_app, clean_database):
    user = UserRepository().create(email="latest@example.com", password="pw-123456")
    repo = DataSetRepository()

    def make(version, doi, origin_id=None):
        meta = DSMetaDataRepository().create(
            title=f"v{version}", description="d", publication_type=PublicationType.BOOK, dataset_doi=doi
        )
        return repo.create(
            user_id=user.id, ds_meta_data_id=meta.id, dataset_version=version, dataset_origin_id=origin_id
        )

    v1 = make(1, "10.1/v1")
    v2 = make(2, "10.1/v2", origin_id=v1.id)
    v3 = make(3, "10.1/v3", origin_id=v2.id)
    standalone = make(1, "10.1/solo")

    ids = {d.id for d in repo.get_synchronized_datasets_by_user(user.id)}

    # Only the tip of the lineage (v3) and the un-versioned dataset show up.
    assert v3.id in ids
    assert standalone.id in ids
    assert v1.id not in ids
    assert v2.id not in ids
    # A dataset with no lineage reports no versions.
    assert standalone.has_versions() is False


def _lineage_with_concept_doi(email, concept_doi, versions=2):
    user = UserRepository().create(email=email, password="pw-123456")
    repo = DataSetRepository()
    created = []
    origin_id = None
    for version in range(1, versions + 1):
        meta = DSMetaDataRepository().create(
            title=f"v{version}",
            description="d",
            publication_type=PublicationType.BOOK,
            dataset_doi=f"10.5072/zenodo.{version}",
            dataset_concept_doi=concept_doi,
        )
        dataset = repo.create(
            user_id=user.id, ds_meta_data_id=meta.id, dataset_version=version, dataset_origin_id=origin_id
        )
        created.append(dataset)
        origin_id = dataset.id
    return created


def test_get_by_concept_doi_returns_the_oldest_version(test_app, clean_database):
    v1, v2 = _lineage_with_concept_doi("concept@example.com", "10.5072/zenodo.0")

    found = DataSetRepository().get_by_concept_doi("10.5072/zenodo.0")

    assert found.id == v1.id
    assert [dataset.id for dataset in found.all_versions()] == [v1.id, v2.id]


def test_get_by_concept_doi_is_none_for_unknown_or_empty_values(test_app, clean_database):
    _lineage_with_concept_doi("concept2@example.com", "10.5072/zenodo.0")

    repo = DataSetRepository()

    assert repo.get_by_concept_doi("10.5072/zenodo.404") is None
    assert repo.get_by_concept_doi("") is None
    assert repo.get_by_concept_doi(None) is None


def test_concept_doi_column_tolerates_older_records(test_app, clean_database):
    # Datasets published before the column existed keep it null and stay usable.
    user = UserRepository().create(email="legacy@example.com", password="pw-123456")
    meta = DSMetaDataRepository().create(
        title="legacy", description="d", publication_type=PublicationType.BOOK, dataset_doi="10.5072/zenodo.9"
    )
    dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=meta.id)

    assert dataset.ds_meta_data.dataset_concept_doi is None
    assert dataset.get_concept_doi() is None
    assert dataset.is_latest_version() is True
    assert dataset.latest_version().id == dataset.id
