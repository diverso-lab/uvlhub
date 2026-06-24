import pytest

pytestmark = pytest.mark.unit

from app.features.auth.repositories import UserRepository
from app.features.dataset.models import PublicationType
from app.features.dataset.repositories import DataSetRepository, DSMetaDataRepository
from app.features.featuremodel.repositories import FeatureModelRepository
from app.features.featuremodel.services import FeatureModelService


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


def test_sample_assertion(test_client):
    """
    Sample test to verify that the test framework and environment are working correctly.
    It does not communicate with the Flask application; it only performs a simple assertion to
    confirm that the tests in this module can be executed.
    """
    greeting = "Hello, World!"
    assert greeting == "Hello, World!", "The greeting does not coincide with 'Hello, World!'"


def test_count_feature_models_counts_only_synchronized_datasets(test_client, clean_database):
    user = UserRepository().create(email="models@example.com", password="test1234")

    synced_meta = DSMetaDataRepository().create(
        title="Synced dataset",
        description="Dataset with DOI",
        publication_type=PublicationType.BOOK,
        dataset_doi="10.1234/synced-dataset",
    )
    unsynced_meta = DSMetaDataRepository().create(
        title="Unsynced dataset",
        description="Dataset without DOI",
        publication_type=PublicationType.BOOK,
    )

    synced_dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=synced_meta.id)
    unsynced_dataset = DataSetRepository().create(user_id=user.id, ds_meta_data_id=unsynced_meta.id)

    FeatureModelRepository().create(dataset_id=synced_dataset.id)
    FeatureModelRepository().create(dataset_id=synced_dataset.id)
    FeatureModelRepository().create(dataset_id=unsynced_dataset.id)

    assert FeatureModelService().count_feature_models() == 2
